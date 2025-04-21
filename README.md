# 文件搜索工具 (File Search Tool)

一个简单但功能强大的文件内容搜索工具，提供 Python GUI 版本和 Web 版本两种实现。

## Python GUI 版本

<img width="1194" alt="image" src="https://github.com/user-attachments/assets/47d49cc8-125a-4cab-822e-3a0e7f77bdde" />

### 功能特点

- 🔍 实时文件内容搜索
- 🎯 多关键字搜索支持（使用逗号分隔）
- 💡 搜索结果黄色高亮显示
- 📝 支持大文件搜索
- 🌈 美观的图形界面
- �� 支持 UTF-8 和 GBK 编码
- 📊 支持日志文件（.log）分析
- 📈 保持原始日志格式和结构

### 支持的文件类型

- 📝 文本文件 (.txt)
- 📋 日志文件 (.log)
- 🔧 配置文件 (.conf, .ini)
- 📜 其他文本格式文件

### 系统要求

- Python 3.6+
- PyQt6

### 安装依赖

```bash
pip install PyQt6 PyQt6-Qt6 PyQt6-sip
```

### macOs15

```bash
python -m venv venv && source venv/bin/activate && pip install --no-cache-dir --force-reinstall PyQt6 PyQt6-Qt6 PyQt6-sip
```

### 运行方式

```bash
python search_gui.py
```

### 使用说明

1. 点击"选择文件"按钮选择要搜索的文件
2. 在搜索框中输入关键字（多个关键字用逗号分隔）
3. 点击"搜索"按钮开始搜索
4. 匹配内容会在右侧文本框中以黄色高亮显示

## HTML 版本

<img width="1415" alt="image" src="https://github.com/user-attachments/assets/90ad7f41-5ec2-4196-a651-06bff75fdc5e" />

### 功能特点

- 🌐 无需安装，浏览器直接运行
- 📱 响应式设计，支持移动设备
- ⚡ 纯前端实现，无需服务器
- 🎨 简洁现代的界面设计
- 搜索速度慢，所以用Cursor写了python版本

### 使用方法

1. 直接在浏览器中打开 `search.html` 文件
2. 点击"选择文件"或将文件拖拽到指定区域
3. 在搜索框中输入关键字
4. 搜索结果会实时显示并高亮

### 浏览器兼容性

- ✅ Chrome 60+
- ✅ Firefox 60+
- ✅ Safari 12+
- ✅ Edge 79+

## 注意事项

- 大文件搜索时可能需要等待一段时间
- 建议文件大小不超过 100MB
- 如遇到编码问题，请尝试使用记事本另存为 UTF-8 编码

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个工具。

## 许可证

MIT License

