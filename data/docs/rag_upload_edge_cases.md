# RAG Upload Edge Cases

RAG 上传失败不一定是解析失败，也可能是 embedding、chunking 或向量写入阶段的问题。

常见混淆包括：

- OCR 成功但 chunk 过大
- embedding 成功但 index write 失败
- 文件上传成功但检索向量为空
- 把文档解析错误误判成权限问题

排查时应依次检查解析、分块、embedding、写入和检索链路。
