#!/usr/bin/env python3
import mmap
import os
import sys
import re
import argparse
from typing import List, Iterator, Tuple
import time
from datetime import datetime
from pathlib import Path
import signal
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
import itertools

# ANSI 颜色代码
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    HIGHLIGHT = '\033[43m\033[30m'  # 黄底黑字

class SearchResult:
    def __init__(self, line_num: int, line: str, matches: List[Tuple[int, int]]):
        self.line_num = line_num
        self.line = line
        self.matches = matches

def create_pattern(keywords: List[str]) -> str:
    """创建正则表达式模式"""
    escaped_keywords = [re.escape(kw) for kw in keywords]
    return '|'.join(f'({kw})' for kw in escaped_keywords)

def highlight_matches(line: str, matches: List[Tuple[int, int]]) -> str:
    """高亮匹配的文本"""
    if not matches:
        return line
    
    result = []
    last_end = 0
    for start, end in sorted(matches):
        result.append(line[last_end:start])
        result.append(f"{Colors.HIGHLIGHT}{line[start:end]}{Colors.ENDC}")
        last_end = end
    result.append(line[last_end:])
    return ''.join(result)

def search_chunk(chunk: bytes, pattern: str, line_queue: Queue, 
                start_pos: int = 0, encoding: str = 'utf-8') -> None:
    """搜索文件块中的匹配项"""
    try:
        text = chunk.decode(encoding)
        regex = re.compile(pattern)
        
        for i, line in enumerate(text.splitlines(), 1):
            matches = []
            for match in regex.finditer(line):
                matches.append((match.start(), match.end()))
            if matches:
                line_queue.put(SearchResult(i + start_pos, line, matches))
    except UnicodeDecodeError:
        pass  # 忽略解码错误

def count_lines_before(mm: mmap.mmap, pos: int) -> int:
    """计算指定位置之前的行数"""
    return mm[:pos].count(b'\n')

def process_file(file_path: str, keywords: List[str], chunk_size: int = 1024*1024) -> Iterator[SearchResult]:
    """处理文件并返回搜索结果"""
    pattern = create_pattern(keywords)
    results_queue = Queue()
    
    try:
        with open(file_path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            file_size = mm.size()
            
            # 创建线程池
            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                # 提交搜索任务
                futures = []
                for i in range(0, file_size, chunk_size):
                    chunk = mm[i:min(i + chunk_size, file_size)]
                    start_line = count_lines_before(mm, i)
                    futures.append(executor.submit(
                        search_chunk, chunk, pattern, results_queue, start_line
                    ))
                
                # 获取结果
                while futures or not results_queue.empty():
                    if not results_queue.empty():
                        yield results_queue.get()
                    
                    # 检查完成的任务
                    futures = [f for f in futures if not f.done()]
                    
            mm.close()
    except Exception as e:
        print(f"{Colors.RED}Error processing file {file_path}: {str(e)}{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description='Fast file search tool')
    parser.add_argument('file', help='File to search in')
    parser.add_argument('keywords', nargs='+', help='Keywords to search for')
    parser.add_argument('-c', '--context', type=int, default=0,
                      help='Number of context lines to show')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"{Colors.RED}File not found: {args.file}{Colors.ENDC}")
        return

    file_size = os.path.getsize(args.file)
    start_time = time.time()
    
    print(f"{Colors.HEADER}Searching in: {args.file} ({file_size/1024/1024:.2f} MB){Colors.ENDC}")
    print(f"{Colors.BLUE}Keywords: {', '.join(args.keywords)}{Colors.ENDC}\n")

    try:
        match_count = 0
        for result in process_file(args.file, args.keywords):
            match_count += 1
            print(f"{Colors.GREEN}{result.line_num:>6}{Colors.ENDC}: "
                  f"{highlight_matches(result.line, result.matches)}")
            
        duration = time.time() - start_time
        print(f"\n{Colors.HEADER}Found {match_count} matches in {duration:.2f} seconds{Colors.ENDC}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Search interrupted by user{Colors.ENDC}")
        sys.exit(1)

if __name__ == '__main__':
    main()
