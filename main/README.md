# 文件哈希读取API

这是一个基于FastAPI实现的文件哈希计算服务，提供以下功能：

- 计算上传文件的哈希值
- 计算服务器上指定路径文件的哈希值
- 批量计算目录中文件的哈希值
- 获取支持的哈希算法列表

## 安装

```bash
pip install -r requirements.txt
```

## 运行服务

```bash
python file_hash_api_server.py
```

服务默认会在 http://0.0.0.0:8000 上启动。

## API端点

- `GET /`: 欢迎信息
- `POST /api/v1/hash/file`: 计算上传文件的哈希值
- `GET /api/v1/hash/algorithms`: 获取支持的哈希算法列表
- `POST /api/v1/hash/path`: 计算指定路径文件的哈希值
- `POST /api/v1/hash/batch`: 异步处理目录中的文件
- `GET /api/v1/hash/batch/{task_id}`: 获取批处理任务的状态
- `GET /api/v1/hash/batch/{task_id}/results`: 获取批处理任务的结果

## API文档

服务运行后，可以访问以下URL查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 