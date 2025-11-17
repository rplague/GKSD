from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time

def search_from_zgbk(target):
	"""基于https://www.zgbk.com/的词典系统 - 使用Playwright获取完整HTML"""
	base_url = "https://www.zgbk.com"
	search_url = f"{base_url}/ecph/search/result?SiteID=1&Alias=all&Query={target}"

	try:
		with sync_playwright() as p:
			link = None
			# 启动浏览器（无头模式）
			browser = p.chromium.launch(headless=True)
			
			# 创建新页面
			page = browser.new_page()
			
			# 设置用户代理，模拟真实浏览器
			page.set_extra_http_headers({
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
				"Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3"
			})
			
			# 访问搜索页面
			page.goto(search_url, wait_until="networkidle")
			
			try:
				page.wait_for_selector('.part-list li', timeout=15000)
			except:
				return None
			
			page.wait_for_load_state('networkidle')
			
			page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
			time.sleep(0.3)
			
			# 获取完整的HTML内容
			html_content = page.content()
			
			# 关闭浏览器
			browser.close()
	
		
		# 使用BeautifulSoup解析获取的内容
		soup = BeautifulSoup(html_content, 'html.parser')
		result_parent = soup.find("ul", class_="part-list clearfix", id="test")
		title_items = result_parent.find_all("h2", class_="ellipsis fl")
		for item in title_items:
			title = item["title"]
			title = [i for i in title.split("/") if i]
			if title[0] == target:
				link_item = item.find("a", class_="font20 search-title")
				link = link_item["href"]
		if not link:
			return None
	except Exception as e:
		raise e
	search_url = link
	try:
		with sync_playwright() as p:
			# 启动浏览器（无头模式）
			browser = p.chromium.launch(headless=True)
			
			# 创建新页面
			page = browser.new_page()
			
			# 设置用户代理，模拟真实浏览器
			page.set_extra_http_headers({
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
				"Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3"
			})
			
			# 访问搜索页面
			basic_program.log_message(f"正在访问: {search_url}", printing = False)
			page.goto(search_url, wait_until="networkidle")
			
			try:
				page.wait_for_selector('div.summary.fontsize', timeout=15000)
			except:
				return None
			
			page.wait_for_load_state('networkidle')
			
			page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
			time.sleep(0.3)
			
			# 获取完整的HTML内容
			html_content = page.content()
			
			# 关闭浏览器
			browser.close()
	
		
		# 使用BeautifulSoup解析获取的内容
		soup = BeautifulSoup(html_content, 'html.parser')
		result_parent = soup.find("p", style="text-indent: 2em;").get_text(strip=True)
		return result_parent
	except Exception as e:
		raise e

if __name__ == "__main__":
	print(search_from_zgbk("器械体操"))