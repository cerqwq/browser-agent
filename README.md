# 🌐 Browser Agent

浏览器自动化Agent，受browser-use启发，支持AI驱动的浏览器操作。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" />
  <img src="https://img.shields.io/badge/Playwright-Browser-green?logo=playwright" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

## ✨ 特性

- 🧭 智能网页导航
- 🖱️ 元素交互（点击、输入）
- 📄 内容提取
- 🔍 Google搜索集成
- 📸 页面截图
- 🤖 自然语言指令执行

## 🚀 快速开始

```bash
# 安装依赖
pip install playwright openai
playwright install chromium

# 设置API密钥
export OPENAI_API_KEY=your_key

# 运行
python browser_agent.py
```

## 📖 使用示例

```python
from browser_agent import BrowserAgentWithLLM

# 创建Agent
agent = BrowserAgentWithLLM(model="mimo-v2.5-pro")
agent.start()

# 自然语言指令
result = agent.execute_instruction("打开百度搜索Python教程")
result = agent.execute_instruction("点击搜索按钮")
result = agent.execute_instruction("截图")

# 直接操作
agent.navigate("https://example.com")
content = agent.get_content("body")
links = agent.get_links()
agent.screenshot("page.png")

# Google搜索
results = agent.search_agent("Python最佳实践")

agent.stop()
```

## 🔧 支持的操作

| 操作 | 说明 |
|------|------|
| `navigate` | 导航到URL |
| `click` | 点击元素 |
| `type` | 输入文本 |
| `get_content` | 获取页面内容 |
| `get_links` | 获取所有链接 |
| `screenshot` | 页面截图 |
| `evaluate` | 执行JavaScript |
| `search_google` | Google搜索 |

## 📁 项目结构

```
browser-agent/
├── browser_agent.py  # 浏览器Agent核心
├── screenshots/      # 截图存储
└── README.md
```

## 📄 许可证

MIT License
