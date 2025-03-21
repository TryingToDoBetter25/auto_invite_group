# encoding:utf-8
import os
import json
import re
import requests
import config
from common.log import logger
import plugins  # 先导入plugins模块
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *  # 再导入所有插件类

@plugins.register(
    name="AutoInviteGroup",
    desire_priority=200,  # 提高优先级
    hidden=False,
    enabled=True,
    desc="自动邀请用户进群插件",
    version="0.1.0",
    author="Danny",
)
class AutoInviteGroup(Plugin):
    # 配置项
    auto_invite = True
    keyword_mappings = []
    invite_after_accept = False
    fuzzy_match = True  # 添加模糊匹配选项
    match_threshold = 0.7  # 相似度阈值
    
    def __init__(self):
        super().__init__()
        try:
            # 从主配置文件读取API相关参数
            conf = config.conf()
            
            # 读取API相关配置项
            self.api_base_url = conf.get("gewechat_base_url", "")
            self.api_token = conf.get("gewechat_token", "")
            self.app_id = conf.get("gewechat_app_id", "")
            
            logger.info(f"[AutoInviteGroup] 从主配置读取: api_base_url={self.api_base_url}, app_id={self.app_id}")
            
            # 加载插件配置文件
            plugin_config_path = os.path.join(self.path, "auto_invite_group-config.json")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                    logger.info(f"[AutoInviteGroup] 成功加载配置文件: {plugin_config_path}")
            else:
                logger.warning(f"[AutoInviteGroup] 配置文件不存在: {plugin_config_path}，将使用默认配置")
                self.config = {
                    "auto_invite": True,
                    "invite_after_accept": False,
                    "fuzzy_match": True,
                    "match_threshold": 0.7,
                    "keyword_mappings": [
                        {"keyword": "群", "group_id": "12345678@chatroom", "reason": "欢迎加入我们的群聊"}
                    ]
                }
            
            # 读取插件自身配置项
            self.auto_invite = self.config.get("auto_invite", self.auto_invite)
            self.keyword_mappings = self.config.get("keyword_mappings", self.keyword_mappings)
            self.invite_after_accept = self.config.get("invite_after_accept", self.invite_after_accept)
            self.fuzzy_match = self.config.get("fuzzy_match", self.fuzzy_match)
            self.match_threshold = self.config.get("match_threshold", self.match_threshold)
            
            # 注册事件处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info(f"[AutoInviteGroup] 已初始化完成，auto_invite={self.auto_invite}, keyword_mappings={self.keyword_mappings}")
        except Exception as e:
            logger.error(f"[AutoInviteGroup] 初始化异常：{e}")
            raise Exception(f"[AutoInviteGroup] 初始化失败: {e}")

    # 在类中添加一个模糊匹配方法
    def _fuzzy_match(self, keyword, text):
        """模糊匹配关键词"""
        # 使用正则表达式进行模糊匹配
        if self.fuzzy_match:
            # 宽松匹配 - 关键词中的每个字符都可以被中间的任意字符隔开
            pattern = '.*'.join(list(keyword))
            if re.search(pattern, text, re.IGNORECASE):
                logger.info(f"[AutoInviteGroup] 模糊匹配成功: 文本='{text}', 关键词='{keyword}', 模式='{pattern}'")
                return True
                
            # 尝试部分匹配 - 只要包含关键词的一部分也算匹配
            if len(keyword) > 2:  # 关键词较长时
                if keyword[:2] in text or keyword[-2:] in text:
                    logger.info(f"[AutoInviteGroup] 部分匹配成功: 文本='{text}', 关键词='{keyword}'")
                    return True
            
            return False
        else:
            # 保留精确匹配选项
            return keyword in text

    def on_handle_context(self, e_context: EventContext):
        # 详细日志
        logger.info(f"[AutoInviteGroup] 收到消息处理事件")
        
        if not self.auto_invite:
            logger.info("[AutoInviteGroup] 自动邀请功能未开启")
            return
            
        context = e_context["context"]
        
        # 处理包含关键词的消息
        if context.type != ContextType.TEXT:
            logger.info(f"[AutoInviteGroup] 消息类型不是TEXT，而是{context.type}，跳过")
            return
            
        content = context.content
        logger.info(f"[AutoInviteGroup] 处理文本消息：{content}")
        
        # 从context中获取msg对象
        msg = context.kwargs.get("msg")
        if not msg:
            logger.info("[AutoInviteGroup] 消息对象为空，跳过")
            return
        
        # 尝试不同方式获取发送者ID
        sender_id = None
        
        # 尝试从context获取
        if 'session_id' in context.kwargs:
            sender_id = context.kwargs['session_id']
            logger.info(f"[AutoInviteGroup] 从session_id获取发送者ID: {sender_id}")
        
        # 尝试从msg对象获取
        if not sender_id:
            # 打印msg对象的所有属性帮助调试
            logger.info(f"[AutoInviteGroup] msg对象属性: {dir(msg)}")
            
            # 尝试各种可能的属性名
            for attr in ['from_user_id', 'from_wxid', 'FromUserName']:
                try:
                    value = getattr(msg, attr, None)
                    if value:
                        logger.info(f"[AutoInviteGroup] 从{attr}获取值: {value}")
                        if isinstance(value, dict) and 'string' in value:
                            sender_id = value['string']
                        else:
                            sender_id = value
                        break
                except:
                    continue
        
        if not sender_id:
            logger.error("[AutoInviteGroup] 无法获取发送者ID，跳过处理")
            return
            
        logger.info(f"[AutoInviteGroup] 最终确定的发送者ID: {sender_id}")
            
        # 检查消息内容是否包含关键词
        for mapping in self.keyword_mappings:
            keyword = mapping.get("keyword", "")
            if not keyword:
                continue
                
            # 使用模糊匹配方法替代精确匹配
            if self._fuzzy_match(keyword, content):
                group_id = mapping.get("group_id", "")
                reason = mapping.get("reason", "")
                
                if not group_id:
                    logger.info(f"[AutoInviteGroup] 找到关键词 {keyword}，但群ID为空，跳过")
                    continue
                    
                logger.info(f"[AutoInviteGroup] 模糊匹配到关键词 {keyword}，准备邀请用户 {sender_id} 进群 {group_id}")
                    
                try:
                    # 调用API邀请用户进群
                    result = self._invite_to_group(sender_id, group_id, reason)
                    
                    reply = Reply(ReplyType.TEXT, f"已邀请您加入群聊，请查看群邀请通知")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                    logger.info(f"[AutoInviteGroup] 已邀请用户 {sender_id} 进群 {group_id}")
                    return
                    
                except Exception as e:
                    logger.error(f"[AutoInviteGroup] 邀请用户进群异常：{e}")
                    reply = Reply(ReplyType.ERROR, f"邀请进群失败: {str(e)}")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                    return

    def _invite_to_group(self, wxid, group_id, reason=""):
        """调用API邀请用户进群"""
        logger.info(f"[AutoInviteGroup] 调用API邀请用户 {wxid} 进群 {group_id}")
        url = f"{self.api_base_url}/group/inviteMember"
        headers = {
            "X-GEWE-TOKEN": self.api_token,
            "Content-Type": "application/json"
        }
        payload = {
            "appId": self.app_id,
            "wxids": wxid,
            "chatroomId": group_id,
            "reason": reason
        }
        
        logger.info(f"[AutoInviteGroup] 请求URL: {url}")
        logger.info(f"[AutoInviteGroup] 请求payload: {payload}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        logger.info(f"[AutoInviteGroup] API响应状态码: {response.status_code}")
        logger.info(f"[AutoInviteGroup] API响应内容: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.text}")
            
        result = response.json()
        if result.get("ret") != 200:
            raise Exception(f"API响应错误: {result.get('msg')}")
            
        logger.info(f"[AutoInviteGroup] 成功邀请用户 {wxid} 进群 {group_id}")
        return result

    def get_help_text(self, verbose=False, **kwargs):
        help_text = "自动邀请用户进群插件\n"
        if verbose:
            help_text += "功能：当用户发送包含特定关键词的消息时，自动邀请其进入指定群聊\n"
            help_text += "配置：\n"
            help_text += "- auto_invite: 是否开启自动邀请功能\n"
            help_text += "- keyword_mappings: 关键词与群ID的映射关系\n"
            help_text += "- invite_after_accept: 是否在添加好友成功后自动邀请进群\n"
            help_text += "- fuzzy_match: 是否启用模糊匹配\n"
            help_text += "- match_threshold: 匹配阈值"
        return help_text
