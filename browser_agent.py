"""
Browser Agent - 浏览器自动化Agent
受 browser-use 启发，支持AI驱动的浏览器操作
"""

import json
import os
from typing import Dict, List, Optional, Generator
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[警告] playwright未安装，浏览器功能不可用")


class BrowserAgent:
    """
    浏览器自动化Agent
    支持：网页导航、元素交互、信息提取、截图
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional['Browser'] = None
        self.page: Optional['Page'] = None
        self.playwright = None
        self.history: List[Dict] = []

    def start(self):
        """启动浏览器"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("playwright未安装")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        print("[Browser] 浏览器已启动")

    def stop(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("[Browser] 浏览器已关闭")

    def navigate(self, url: str) -> str:
        """导航到URL"""
        if not self.page:
            return "浏览器未启动"

        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = self.page.title()
            self._log("navigate", url)
            return f"已导航到: {title} ({url})"
        except Exception as e:
            return f"导航失败: {e}"

    def get_content(self, selector: str = "body") -> str:
        """获取页面内容"""
        if not self.page:
            return "浏览器未启动"

        try:
            element = self.page.query_selector(selector)
            if element:
                text = element.inner_text()
                return text[:5000]  # 限制长度
            return f"未找到元素: {selector}"
        except Exception as e:
            return f"获取内容失败: {e}"

    def get_links(self) -> List[Dict]:
        """获取页面所有链接"""
        if not self.page:
            return []

        try:
            links = self.page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    text: a.innerText.trim().substring(0, 100),
                    href: a.href
                })).filter(l => l.text && l.href)
            """)
            return links[:50]  # 限制数量
        except Exception as e:
            return [{"error": str(e)}]

    def click(self, selector: str) -> str:
        """点击元素"""
        if not self.page:
            return "浏览器未启动"

        try:
            self.page.click(selector, timeout=5000)
            self._log("click", selector)
            return f"已点击: {selector}"
        except Exception as e:
            return f"点击失败: {e}"

    def type_text(self, selector: str, text: str) -> str:
        """输入文本"""
        if not self.page:
            return "浏览器未启动"

        try:
            self.page.fill(selector, text)
            self._log("type", f"{selector}: {text[:50]}")
            return f"已输入: {text[:50]}..."
        except Exception as e:
            return f"输入失败: {e}"

    def screenshot(self, path: str = None) -> str:
        """截图"""
        if not self.page:
            return "浏览器未启动"

        try:
            if not path:
                path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.page.screenshot(path=path)
            self._log("screenshot", path)
            return f"截图已保存: {path}"
        except Exception as e:
            return f"截图失败: {e}"

    def evaluate(self, expression: str) -> str:
        """执行JavaScript"""
        if not self.page:
            return "浏览器未启动"

        try:
            result = self.page.evaluate(expression)
            return str(result)
        except Exception as e:
            return f"执行失败: {e}"

    def search_google(self, query: str) -> List[Dict]:
        """Google搜索"""
        self.navigate(f"https://www.google.com/search?q={query}")
        results = self.evaluate("""
            () => Array.from(document.querySelectorAll('div.g')).slice(0, 5).map(div => ({
                title: div.querySelector('h3')?.innerText || '',
                url: div.querySelector('a')?.href || '',
                snippet: div.querySelector('.VwiC3b')?.innerText || ''
            }))
        """)
        try:
            return json.loads(results)
        except:
            return [{"raw": results}]

    def _log(self, action: str, detail: str):
        """记录操作历史"""
        self.history.append({
            "action": action,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })

    def get_history(self) -> List[Dict]:
        """获取操作历史"""
        return self.history

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


class BrowserAgentWithLLM(BrowserAgent):
    """
    带LLM的浏览器Agent
    可以理解自然语言指令并执行浏览器操作
    """

    def __init__(self, model: str = "mimo-v2.5-pro", **kwargs):
        super().__init__(**kwargs)
        self.model = model
        from openai import OpenAI
        self.client = OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY', ''),
            base_url=os.environ.get('OPENAI_BASE_URL', 'https://api.xiaomimimo.com/v1')
        )

    def execute_instruction(self, instruction: str) -> str:
        """执行自然语言指令"""
        # 获取当前页面状态
        current_url = self.page.url if self.page else "无"
        current_title = self.page.title() if self.page else "无"
        links = self.get_links()[:10]

        prompt = f"""你是一个浏览器自动化助手。根据用户指令，生成相应的浏览器操作。

当前页面：
- URL: {current_url}
- 标题: {current_title}
- 可用链接: {json.dumps(links[:5], ensure_ascii=False)}

用户指令: {instruction}

请返回JSON格式的操作指令：
{{"action": "navigate|click|type|screenshot|get_content|evaluate", "params": {{...}}}}

示例：
- 导航: {{"action": "navigate", "params": {{"url": "https://example.com"}}}}
- 点击: {{"action": "click", "params": {{"selector": "button.submit"}}}}
- 输入: {{"action": "type", "params": {{"selector": "input#search", "text": "搜索内容"}}}}
- 获取内容: {{"action": "get_content", "params": {{"selector": "body"}}}}
- 截图: {{"action": "screenshot", "params": {{}}}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        try:
            content = response.choices[0].message.content
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                action_data = json.loads(json_match.group())
                action = action_data.get("action")
                params = action_data.get("params", {})

                # 执行操作
                if action == "navigate":
                    return self.navigate(params.get("url", ""))
                elif action == "click":
                    return self.click(params.get("selector", ""))
                elif action == "type":
                    return self.type_text(params.get("selector", ""), params.get("text", ""))
                elif action == "screenshot":
                    return self.screenshot(params.get("path"))
                elif action == "get_content":
                    return self.get_content(params.get("selector", "body"))
                elif action == "evaluate":
                    return self.evaluate(params.get("expression", ""))
                else:
                    return f"未知操作: {action}"
        except Exception as e:
            return f"指令解析失败: {e}"

        return "无法理解指令"

    def research_topic(self, topic: str) -> str:
        """研究主题"""
        results = self.search_google(topic)
        summary = f"搜索 '{topic}' 的结果:\n\n"
        for i, r in enumerate(results, 1):
            if isinstance(r, dict) and 'title' in r:
                summary += f"{i}. {r['title']}\n   {r.get('snippet', '')}\n   {r.get('url', '')}\n\n"
        return summary


if __name__ == "__main__":
    if not PLAYWRIGHT_AVAILABLE:
        print("请安装playwright: pip install playwright && playwright install chromium")
        exit(1)

    print("Browser Agent 已启动")
    print("输入URL导航，或自然语言指令")
    print()

    agent = BrowserAgentWithLLM(headless=False)
    agent.start()

    try:
        while True:
            try:
                instruction = input("指令: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not instruction:
                continue
            if instruction.lower() in ("quit", "exit"):
                break

            # 如果是URL，直接导航
            if instruction.startswith(("http://", "https://", "www.")):
                result = agent.navigate(instruction)
            else:
                result = agent.execute_instruction(instruction)

            print(result)
            print()

    finally:
        agent.stop()
