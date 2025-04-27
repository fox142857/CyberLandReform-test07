#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件哈希API服务启动脚本
----------------
用于启动文件哈希计算的FastAPI服务
"""

import os
import sys
import uvicorn

def main():
    """启动文件哈希API服务"""
    # 确保src目录在模块搜索路径中
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
    
    # 启动FastAPI服务
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    
    print(f"启动文件哈希计算API服务于 http://{host}:{port}")
    uvicorn.run(
        "src.api.file_hash_api:app",  # 更新导入路径
        host=host,
        port=port,
        reload=True,  # 开发模式下可以热重载
        log_level="info"
    )

if __name__ == "__main__":
    main() 