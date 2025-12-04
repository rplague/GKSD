import os
import datetime
import json
from typing import List, Tuple, Any, Optional, Union, Dict

class Colors:
	"""颜色常量类 - 用于终端文字颜色设置"""
	
	# 前景色（文字颜色）
	RED = '\033[91m'        # 红色
	GREEN = '\033[92m'      # 绿色
	YELLOW = '\033[93m'     # 黄色
	BLUE = '\033[94m'       # 蓝色
	MAGENTA = '\033[95m'    # 洋红色/紫色
	CYAN = '\033[96m'       # 青色/蓝绿色
	WHITE = '\033[97m'      # 白色
	RESET = '\033[0m'       # 重置所有颜色和样式（恢复默认）
	
	# 背景色
	BG_BLACK = '\033[40m'   # 黑色背景
	BG_RED = '\033[41m'     # 红色背景
	BG_GREEN = '\033[42m'   # 绿色背景
	BG_YELLOW = '\033[43m'  # 黄色背景
	BG_BLUE = '\033[44m'    # 蓝色背景
	BG_MAGENTA = '\033[45m' # 洋红色背景
	BG_CYAN = '\033[46m'    # 青色背景
	BG_WHITE = '\033[47m'   # 白色背景
	BG_RESET = '\033[49m'   # 重置背景色（恢复默认背景）

def log_message(
	content: str,
	level_int: int = 20,
	printing: bool = True):
	"""
	日志记录函数

	记录日志信息到终端和文件
	
	参数:
		content (str): 日志内容
		level_int (int): 日志等级
			0   重要信息
			10  调试信息
			20  程序运行信息（默认级别）
			30  警告信息
			40  错误，但程序仍可运行
			50  严重错误，程序可能无法继续运行
		printing (bool): 是否打印到终端

	报错:
		ValueError: 日志内容未能获取
	"""
	# 输入验证
	if not content:
		raise ValueError("日志内容不能为空")
	# 获取当前时间
	current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	# 转换日志等级
	if    level_int ==  0:
		level = "IMPORTANT"
		color = Colors.RESET
		bg_color = Colors.BG_GREEN
	elif  level_int <= 10:
		level = "+"
		color = Colors.CYAN
		bg_color = Colors.BG_RESET
	elif  level_int <= 20:
		level = "-"
		color = Colors.RESET
		bg_color = Colors.BG_RESET
	elif  level_int <= 30:
		level = "*"
		color = Colors.YELLOW
		bg_color = Colors.BG_RESET
	elif  level_int <= 40:
		level = "!"
		color = Colors.RED
		bg_color = Colors.BG_RESET
	else             :
		level = " CRITICAL"
		color = Colors.RESET
		bg_color = Colors.BG_RED

	# 格式化终端输出并输出到终端
	terminal_output = f"{color}{bg_color}[{level}]{Colors.RESET} {content}"
	if printing: print(terminal_output)
	
	# 格式化文件输出（包含时间戳）
	file_output = f"[{level}] {current_time} \n    MESSAGE: {content}"
	
	# 写入到log.md文件（追加模式）
	with open("log.md", "a", encoding="utf-8") as log_file:
		log_file.write(file_output + "\n")


def boot():
	"""
	检查并确定系统的基本运行条件
	
	该函数用于验证程序运行所需的基础环境配置
	
	Returns:
		bool: 如果所有基本运行条件满足或可修复则返回True，否则返回False
	"""
	try:
		# 确定日志系统
		if not os.path.exists("log.md"):
			print(f"[!] 日志系统错误\n    开始重建")
			with open("log.md", 'w', encoding='utf-8') as file:
				print("    log.md重建..........完成")
				pass
			log_message("系统开机", 0, False)
			log_message("重建日志系统", printing = False)
			print("    日志系统测试........完成")
		else:
			log_message("系统开机", 0, False)
			log_message("日志系统自检")

		log_message("boot全部完成")
		return True
	except Exception as e:
		print(f"[!] boot错误 {str(e)}")
		return False


def init_program():
	"""
	检查并确定系统的各个运行文件
	
	Returns:
		bool: 如果所有基本运行条件满足或可修复则返回True，否则返回False
	"""
	try:
		if not _check_and_create_config():
			return False
			
		# 可以添加其他初始化检查
		# if not _check_module_directory():
		# 	return False
			
		log_message("初始化全部完成")
		return True
	except Exception as e:
		log_message(f"初始化错误: {str(e)}", 50)
		return False


def _check_and_create_config():
	"""检查并创建配置文件"""
	config_file = "config.json"
	
	# 如果配置文件存在，验证其完整性
	if os.path.exists(config_file):
		try:
			with open(config_file, 'r', encoding='utf-8') as file:
				config = json.load(file)
			
			# 检查必需字段
			required_fields = ["database_data", "database_data_v", "target_dict", "module_path", "index", "llm_api"]
			for field in required_fields:
				if field not in config:
					log_message(f"配置文件缺少必需字段: {field}", 40)
					break
			else:  # 所有字段都存在
				return True
				
		except json.JSONDecodeError:
			log_message("配置文件格式错误", 40)
		except Exception as e:
			log_message(f"读取配置文件失败: {str(e)}", 40)
	
	# 配置文件不存在或验证失败，询问用户是否重建
	log_message("配置文件不存在或格式错误", 30)
	answer = input("是否开始重建？[Y/n] ").strip().lower()
	
	if answer == 'n':
		log_message("配置文件取消重建")
		log_message("系统关机", 0)
		return False
	
	# 创建默认配置文件
	try:
		default_config = {
			"database_data": {
				"host": "localhost",
				"user": "your_username",
				"password": "your_password",
				"database": "test_db",
			},
			"database_data_v": {
				"host": "localhost",
				"port": "6333",
				"password": "your_password",
				"database": "test_db",
			},
			"target_dict": "target.txt",
			"index": 0,
			"module_path": "./module/",
			"llm_api": {
				"api_key": "none",
				"base_url": "https://api.deepseek.com/v1"
			}
		}
		
		with open(config_file, 'w', encoding='utf-8') as file:
			json.dump(default_config, file, ensure_ascii=False, indent=4)
		
		log_message("config.json 重建完成")
		return True
	except Exception as e:
		log_message(f"创建配置文件失败: {str(e)}", 50)
		return False