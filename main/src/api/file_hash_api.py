#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件哈希FastAPI应用
---------------
提供文件哈希计算的REST API服务
"""

import os
import time
import hashlib
import uuid
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.file_hash_direct import FileHashCalculator

# 创建FastAPI应用
app = FastAPI(
    title="文件哈希服务API",
    description="提供文件哈希计算服务的RESTful API",
    version="1.0.0"
)

# 存储异步任务信息
batch_tasks: Dict[str, Dict[str, Any]] = {}

# 模型定义
class HashResponse(BaseModel):
    file_name: str
    algorithm: str
    hash_value: str
    processing_time: float

class AlgorithmsResponse(BaseModel):
    algorithms: List[str]

class BatchTaskRequest(BaseModel):
    directory: str
    recursive: bool = False
    algorithm: str = "sha256"

class BatchTaskResponse(BaseModel):
    task_id: str
    status: str
    directory: str
    created_at: str

class BatchTaskStatus(BatchTaskResponse):
    completed_at: Optional[str] = None
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    success_count: Optional[int] = None
    error_count: Optional[int] = None

class FileHashResult(BaseModel):
    file_path: str
    algorithm: str
    hash_value: Optional[str] = None
    status: str
    error_message: Optional[str] = None

class BatchTaskResults(BaseModel):
    task_id: str
    directory: str
    results: List[FileHashResult]

# API路由

@app.get("/")
async def root():
    return {"message": "文件哈希计算服务API"}

@app.post("/api/v1/hash/file", response_model=HashResponse)
async def hash_file(
    file: UploadFile = File(...),
    algorithm: str = Form("sha256"),
    chunk_size: int = Form(4096)
):
    """
    计算上传文件的哈希值
    """
    if algorithm not in hashlib.algorithms_available:
        raise HTTPException(status_code=400, detail=f"不支持的哈希算法: {algorithm}")
    
    try:
        start_time = time.time()
        
        # 创建临时文件
        temp_file_path = f"/tmp/{uuid.uuid4()}"
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 计算哈希值
        calculator = FileHashCalculator(algorithm=algorithm, chunk_size=chunk_size)
        hash_value = calculator.calculate(temp_file_path)
        
        # 删除临时文件
        os.remove(temp_file_path)
        
        processing_time = time.time() - start_time
        
        return HashResponse(
            file_name=file.filename,
            algorithm=algorithm,
            hash_value=hash_value,
            processing_time=round(processing_time, 4)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")

@app.get("/api/v1/hash/algorithms", response_model=AlgorithmsResponse)
async def get_algorithms():
    """
    获取支持的哈希算法列表
    """
    return AlgorithmsResponse(algorithms=sorted(list(hashlib.algorithms_available)))

@app.post("/api/v1/hash/path", response_model=HashResponse)
async def hash_file_path(
    file_path: str = Form(...),
    algorithm: str = Form("sha256"),
    chunk_size: int = Form(4096)
):
    """
    计算指定路径文件的哈希值
    """
    if algorithm not in hashlib.algorithms_available:
        raise HTTPException(status_code=400, detail=f"不支持的哈希算法: {algorithm}")
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    
    try:
        start_time = time.time()
        
        # 计算哈希值
        calculator = FileHashCalculator(algorithm=algorithm, chunk_size=chunk_size)
        hash_value = calculator.calculate(file_path)
        
        processing_time = time.time() - start_time
        
        return HashResponse(
            file_name=os.path.basename(file_path),
            algorithm=algorithm,
            hash_value=hash_value,
            processing_time=round(processing_time, 4)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")

def process_directory(task_id: str, directory: str, recursive: bool, algorithm: str):
    """后台处理目录中的文件"""
    task = batch_tasks[task_id]
    task["status"] = "processing"
    
    results = []
    success_count = 0
    error_count = 0
    
    try:
        files_to_process = []
        
        # 收集要处理的文件
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    files_to_process.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    files_to_process.append(file_path)
        
        task["total_files"] = len(files_to_process)
        task["processed_files"] = 0
        
        # 处理每个文件
        calculator = FileHashCalculator(algorithm=algorithm)
        for file_path in files_to_process:
            try:
                hash_value = calculator.calculate(file_path)
                results.append(FileHashResult(
                    file_path=file_path,
                    algorithm=algorithm,
                    hash_value=hash_value,
                    status="success"
                ))
                success_count += 1
            except Exception as e:
                results.append(FileHashResult(
                    file_path=file_path,
                    algorithm=algorithm,
                    status="error",
                    error_message=str(e)
                ))
                error_count += 1
            
            task["processed_files"] += 1
        
        # 更新任务状态
        task["status"] = "completed"
        task["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        task["success_count"] = success_count
        task["error_count"] = error_count
        task["results"] = results
        
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)

@app.post("/api/v1/hash/batch", response_model=BatchTaskResponse)
async def batch_hash_files(request: BatchTaskRequest, background_tasks: BackgroundTasks):
    """
    异步处理目录中的文件
    """
    if not os.path.isdir(request.directory):
        raise HTTPException(status_code=404, detail=f"目录不存在: {request.directory}")
    
    task_id = str(uuid.uuid4())
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    task = {
        "task_id": task_id,
        "status": "pending",
        "directory": request.directory,
        "created_at": created_at,
        "algorithm": request.algorithm,
        "recursive": request.recursive
    }
    
    batch_tasks[task_id] = task
    
    # 添加后台任务
    background_tasks.add_task(
        process_directory,
        task_id,
        request.directory,
        request.recursive,
        request.algorithm
    )
    
    return BatchTaskResponse(
        task_id=task_id,
        status="pending",
        directory=request.directory,
        created_at=created_at
    )

@app.get("/api/v1/hash/batch/{task_id}", response_model=BatchTaskStatus)
async def get_batch_status(task_id: str):
    """
    获取批处理任务的状态
    """
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail=f"任务未找到: {task_id}")
    
    task = batch_tasks[task_id]
    
    return BatchTaskStatus(
        task_id=task_id,
        status=task["status"],
        directory=task["directory"],
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
        total_files=task.get("total_files"),
        processed_files=task.get("processed_files"),
        success_count=task.get("success_count"),
        error_count=task.get("error_count")
    )

@app.get("/api/v1/hash/batch/{task_id}/results", response_model=BatchTaskResults)
async def get_batch_results(task_id: str):
    """
    获取批处理任务的结果
    """
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail=f"任务未找到: {task_id}")
    
    task = batch_tasks[task_id]
    
    if task["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail=f"任务尚未完成: {task_id}")
    
    if "results" not in task:
        raise HTTPException(status_code=500, detail=f"任务结果不可用: {task_id}")
    
    return BatchTaskResults(
        task_id=task_id,
        directory=task["directory"],
        results=task["results"]
    ) 