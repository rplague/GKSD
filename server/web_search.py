from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time

class ZgbkSearcher:
	def __init__(self, headless=True):
		self.playwright = sync_playwright().start()
		self.browser = self.playwright.chromium.launch(headless=headless)
		self.context = self.browser.new_context(extra_http_headers={
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3"
		})
		self.page = self.context.new_page()

	def search(self, target):
		"""搜索目标词条"""
		base_url = "https://www.zgbk.com"
		search_url = f"{base_url}/ecph/search/result?SiteID=1&Alias=all&Query={target}"
		
		try:
			# 访问搜索页面
			self.page.goto(search_url, wait_until="networkidle")
			
			try:
				self.page.wait_for_selector('.part-list li', timeout=15000)
			except:
				raise Exception("搜索失败 加载超时")
			
			self.page.wait_for_load_state('networkidle')
			self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
			time.sleep(0.3)
			
			# 解析搜索结果
			html_content = self.page.content()
			soup = BeautifulSoup(html_content, 'html.parser')
			result_parent = soup.find("ul", class_="part-list clearfix", id="test")
			
			if not result_parent:
				raise Exception("搜索失败 检索页面未找到目标结构")
				
			title_items = result_parent.find_all("h2", class_="ellipsis fl")
			link = None
			
			for item in title_items:
				title = item["title"]
				title = [i for i in title.split("/") if i]
				if title and title[0] == target:
					link_item = item.find("a", class_="font20 search-title")
					if link_item and link_item.get("href"):
						link = link_item["href"]
						break
			
			if not link:
				raise Exception("搜索失败 未找到目标链接")
			
			self.page.goto(link, wait_until="networkidle")
			
			try:
				self.page.wait_for_selector('div.summary.fontsize', timeout=15000)
			except:
				raise Exception("搜索失败 未找到目标链接")
			
			self.page.wait_for_load_state('networkidle')
			self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
			time.sleep(0.3)
			
			# 获取详情内容
			html_content = self.page.content()
			soup = BeautifulSoup(html_content, 'html.parser')
			result_element = soup.find("p", style="text-indent: 2em;")
			
			return result_element.get_text(strip=True) if result_element else None
			
		except Exception as e:
			raise e

	def close(self):
		"""关闭浏览器和playwright"""
		if self.context:
			self.context.close()
		if self.browser:
			self.browser.close()
		if self.playwright:
			self.playwright.stop()


if __name__ == "__main__":
	searcher = ZgbkSearcher()
	try:
		print("结果:", searcher.search("器械体操"))
		print("第二次搜索:", searcher.search("体育"))
	finally:
		searcher.close()