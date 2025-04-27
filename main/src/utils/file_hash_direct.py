#!/usr/bin/env python3
"""
FileHashDirect 模块
---------------------
提供直接计算文件哈希值的功能，支持 Python 3.11.5 环境下的多种哈希算法和分块读取方式。
"""

import hashlib
import os
import argparse

class FileHashCalculator:
    def __init__(self, algorithm: str = 'sha256', chunk_size: int = 4096):
        """
        初始化 FileHashCalculator 实例

        参数:
          - algorithm (str): 哈希算法，默认 'sha256'
          - chunk_size (int): 每次读取的块大小（字节），默认 4096
        """
        self.algorithm = algorithm.lower()
        self.chunk_size = chunk_size
        if self.algorithm not in hashlib.algorithms_available:
            raise ValueError(f"不支持的哈希算法: {self.algorithm}")

    def calculate(self, file_path: str) -> str:
        """
        计算指定文件的哈希值，并返回十六进制表示。

        参数:
          - file_path (str): 文件路径

        返回:
          - str: 文件的哈希值

        异常:
          - FileNotFoundError: 当文件不存在时
          - ValueError: 当使用的算法不受支持时
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"找不到文件: {file_path}")

        hash_obj = hashlib.new(self.algorithm)
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(self.chunk_size)
                if not data:
                    break
                hash_obj.update(data)
        return hash_obj.hexdigest()

def main():
    parser = argparse.ArgumentParser(
        description="计算文件哈希值，支持 Python 3.11.5 环境下的多种哈希算法及分块读取。"
    )
    parser.add_argument('--file', required=True, help="目标文件路径")
    parser.add_argument('--algorithm', default='sha256', help="使用的哈希算法 (默认：sha256)")
    parser.add_argument('--chunk-size', type=int, default=4096, help="读取块大小（字节，默认：4096）")
    args = parser.parse_args()

    try:
        calculator = FileHashCalculator(algorithm=args.algorithm, chunk_size=args.chunk_size)
        hash_value = calculator.calculate(args.file)
        print(f"文件: {args.file}")
        print(f"哈希算法: {args.algorithm}")
        print(f"哈希值: {hash_value}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    main() 