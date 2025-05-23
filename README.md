# 自动邀请进群插件

基于[Gewechat](https://github.com/Devo919/Gewechat)和[DoW(dify-on-wechat)](https://github.com/hanfangyuan4396/dify-on-wechat)的插件，当用户发送包含特定关键词的消息时，自动邀请用户进入指定的微信群聊。

基于[Gewechat](https://github.com/Devo919/Gewechat)项目的API文档开发，可直接用于[DoW(dify-on-wechat)](https://github.com/hanfangyuan4396/dify-on-wechat)项目中

## 功能特性

- 自动监听用户消息中的关键词
- 匹配到关键词后自动邀请用户进入对应群聊
- 支持多个关键词与群ID的映射关系
- 支持在添加好友成功后自动邀请进群
- 支持模糊匹配关键词，提高识别灵活性
- 可配置邀请进群的说明文字

## 安装方法

1. 将插件文件夹复制到dow的 `plugins` 目录下
2. 更改 `auto_invite_group-config.json` 配置
3. 重启程序或使用 `#scanp` 命令加载插件

## 配置说明

插件从主配置文件读取API相关参数：
- 从主配置文件的`gewechat_base_url`读取API基础URL
- 从主配置文件的`gewechat_token`读取API令牌
- 从主配置文件的`gewechat_app_id`读取设备ID

插件自身配置：
- `auto_invite`: 是否开启自动邀请功能(true/false)
- `invite_after_accept`: 是否在添加好友成功后自动邀请进群(true/false)
- `fuzzy_match`: 是否启用模糊匹配功能(true/false)，开启后可以更灵活地匹配关键词
- `match_threshold`: 模糊匹配的相似度阈值(0.0-1.0)，值越高要求匹配越精确
- `keyword_mappings`: 关键词与群ID的映射关系
  - `keyword`: 触发邀请的关键词
  - `group_id`: 要邀请进入的群ID
  - `reason`: 邀请进群的说明文字

## 使用方法

1. 配置好关键词和对应的群ID
2. 当用户发送包含配置中关键词的消息时，插件会自动邀请该用户进入对应的群聊
   - 如启用模糊匹配，即使关键词中间有其他字符，或只包含部分关键词也能触发
3. 如果开启了`invite_after_accept`功能，在添加好友成功后会自动邀请新好友进入第一个配置的群

## 模糊匹配说明

插件使用以下策略进行模糊匹配：
1. 关键词中的每个字符都可以被中间的任意字符隔开，仍能被匹配
2. 对于较长的关键词，包含关键词前几个或后几个字符也可能触发匹配
3. 可通过调整`match_threshold`配置项调整匹配灵敏度

## 注意事项

- 群ID格式通常为"数字@chatroom"，请确保配置正确的群ID
- 用户需要是好友才能被邀请进群
- 邀请进群需要用户自己确认才能加入

  ![PixPin_2025-03-21_21-20-35](https://github.com/user-attachments/assets/0bcb1b38-5442-4ccd-ba30-939ec17c06b3)

