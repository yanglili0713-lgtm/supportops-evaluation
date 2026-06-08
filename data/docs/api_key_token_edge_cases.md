# API Key and Token Edge Cases

API key 失效不一定等于 key 被删除。

常见混淆包括：

- token 过期但 key 仍有效
- 错误环境变量加载了旧 key
- key 所属套餐已失效
- key 仍存在但权限范围不足

排查时应同时核对：

- API key 状态
- token 状态
- 环境变量来源
- 账户套餐
- 权限作用域
