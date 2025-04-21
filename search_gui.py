#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLineEdit, QTextEdit, 
                           QProgressBar, QFileDialog, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor, QSyntaxHighlighter
import mmap
from typing import List, Tuple
import re
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import time

class SearchWorker(QThread):
    resultFound = pyqtSignal(int, str, list)  # 行号, 行内容, 匹配位置列表
    searchComplete = pyqtSignal(int, float)    # 匹配数量, 耗时
    progressUpdated = pyqtSignal(int)          # 进度值(0-100)

    def __init__(self, file_path: str, keywords: List[str], chunk_size: int = 1024*1024):
        super().__init__()
        self.file_path = file_path
        self.keywords = keywords
        self.chunk_size = chunk_size
        self.is_running = True

    def create_pattern(self, keywords: List[str]) -> str:
        """创建正则表达式模式"""
        escaped_keywords = [re.escape(kw) for kw in keywords]
        return '|'.join(f'({kw})' for kw in escaped_keywords)

    def search_chunk(self, chunk: bytes, pattern: str, start_pos: int = 0,
                    encoding: str = 'utf-8') -> List[tuple]:
        """搜索文件块中的匹配项"""
        results = []
        try:
            text = chunk.decode(encoding)
            regex = re.compile(pattern)
            
            for i, line in enumerate(text.splitlines(), 1):
                matches = []
                for match in regex.finditer(line):
                    matches.append((match.start(), match.end()))
                if matches:
                    results.append((i + start_pos, line, matches))
        except UnicodeDecodeError:
            pass
        return results

    def count_lines_before(self, mm: mmap.mmap, pos: int) -> int:
        """计算指定位置之前的行数"""
        return mm[:pos].count(b'\n')

    def run(self):
        pattern = self.create_pattern(self.keywords)
        start_time = time.time()
        match_count = 0
        
        try:
            with open(self.file_path, 'rb') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                file_size = mm.size()
                
                with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                    futures = []
                    chunks_processed = 0
                    total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
                    
                    # 提交搜索任务
                    for i in range(0, file_size, self.chunk_size):
                        if not self.is_running:
                            break
                            
                        chunk = mm[i:min(i + self.chunk_size, file_size)]
                        start_line = self.count_lines_before(mm, i)
                        future = executor.submit(
                            self.search_chunk, chunk, pattern, start_line
                        )
                        futures.append(future)
                        
                    # 处理结果
                    for future in futures:
                        if not self.is_running:
                            break
                            
                        results = future.result()
                        for line_num, line, matches in results:
                            self.resultFound.emit(line_num, line, matches)
                            match_count += 1
                            
                        chunks_processed += 1
                        progress = int((chunks_processed / total_chunks) * 100)
                        self.progressUpdated.emit(progress)
                        
                mm.close()
                
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            
        duration = time.time() - start_time
        self.searchComplete.emit(match_count, duration)

    def stop(self):
        self.is_running = False

class SearchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_search = None
        self.file_path = None

    def initUI(self):
        self.setWindowTitle('文件搜索工具')
        self.setGeometry(100, 100, 1200, 800)

        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setFixedWidth(400)
        
        # 搜索输入框和按钮
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入搜索关键字，用逗号分隔...')
        self.search_button = QPushButton('搜索')
        self.search_button.clicked.connect(self.start_search)
        
        # 文件上传区域
        self.file_label = QLabel('当前文件：未选择')
        self.file_button = QPushButton('选择文件')
        self.file_button.clicked.connect(self.select_file)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        # 添加组件到左侧面板
        left_layout.addWidget(self.file_label)
        left_layout.addWidget(self.file_button)
        left_layout.addWidget(self.search_input)
        left_layout.addWidget(self.search_button)
        left_layout.addWidget(self.progress_bar)
        left_layout.addStretch()
        
        # 右侧结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # 设置等宽字体
        self.result_text.setFontFamily('Courier New')
        self.result_text.setFontPointSize(12)
        
        # 添加面板到主布局
        layout.addWidget(left_panel)
        layout.addWidget(self.result_text)
        
        main_widget.setLayout(layout)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "所有文件 (*);;文本文件 (*.txt);;日志文件 (*.log)"
        )
        
        if file_path:
            self.file_path = file_path
            file_name = os.path.basename(file_path)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.file_label.setText(f'当前文件：{file_name}\n大小：{size_mb:.2f} MB')
            
            # 加载文件内容到右侧文本框
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.result_text.setPlainText(content)
            except UnicodeDecodeError:
                try:
                    # 如果UTF-8解码失败，尝试其他编码
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                        self.result_text.setPlainText(content)
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"无法读取文件内容：{str(e)}")
                    return
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法读取文件内容：{str(e)}")
                return

    def start_search(self):
        if not self.file_path:
            QMessageBox.warning(self, "警告", "请先选择要搜索的文件！")
            return
            
        keywords = [k.strip() for k in self.search_input.text().split(',') if k.strip()]
        if not keywords:
            QMessageBox.warning(self, "警告", "请输入搜索关键字！")
            return
            
        # 保存原始文件内容
        original_content = self.result_text.toPlainText()
            
        # 清空之前的结果
        self.result_text.clear()
        
        # 停止之前的搜索（如果有）
        if self.current_search and self.current_search.isRunning():
            self.current_search.stop()
            self.current_search.wait()
            
        # 开始新的搜索
        self.search_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # 显示原始内容并准备高亮
        self.result_text.setPlainText(original_content)
        cursor = self.result_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.result_text.setTextCursor(cursor)
        
        # 高亮所有匹配项
        for keyword in keywords:
            if not keyword:
                continue
                
            # 创建高亮格式
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor("#ffeb3b"))
            
            # 查找并高亮所有匹配项
            while cursor.hasSelection() or not cursor.atEnd():
                cursor = self.result_text.document().find(keyword, cursor)
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(highlight_format)
        
        self.search_button.setEnabled(True)
        self.progress_bar.hide()

    def handle_result(self, line_num: int, line: str, matches: List[Tuple[int, int]]):
        cursor = self.result_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # 添加行号
        format_line_num = QTextCharFormat()
        format_line_num.setForeground(QColor("#2196F3"))
        cursor.insertText(f"{line_num:>6}: ", format_line_num)
        
        # 添加带高亮的行内容
        last_end = 0
        for start, end in sorted(matches):
            # 添加非匹配文本
            cursor.insertText(line[last_end:start])
            
            # 添加高亮匹配文本
            format_highlight = QTextCharFormat()
            format_highlight.setBackground(QColor("#ffeb3b"))
            cursor.insertText(line[start:end], format_highlight)
            
            last_end = end
            
        # 添加剩余文本
        cursor.insertText(line[last_end:] + '\n')
        
        # 确保最新的结果可见
        self.result_text.verticalScrollBar().setValue(
            self.result_text.verticalScrollBar().maximum()
        )

    def handle_complete(self, count: int, duration: float):
        self.search_button.setEnabled(True)
        self.progress_bar.hide()
        
        cursor = self.result_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        format_summary = QTextCharFormat()
        format_summary.setForeground(QColor("#4CAF50"))
        cursor.insertText(f"\n找到 {count} 个匹配项，耗时 {duration:.2f} 秒\n", format_summary)

    def handle_progress(self, value: int):
        self.progress_bar.setValue(value)

def main():
    app = QApplication(sys.argv)
    window = SearchWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 