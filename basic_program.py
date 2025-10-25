import os
import datetime
import json
def log_message(content, level = 20, printing = True):
	"""
	记录日志信息到终端和文件
	
	参数:
	level (int): 日志等级
		0   重要信息
		10  调试信息
		20  程序运行信息（默认级别）
		30  警告信息
		40  错误，但程序仍可运行
		50  严重错误，程序可能无法继续运行

	content (str): 日志内容
	"""
	
	# 获取当前时间
	current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	# 转换日志等级
	if level ==  0: level = "IMPORTANT"
	if level == 10: level = "+"
	if level == 20: level = "-"
	if level == 30: level = "*"
	if level == 40: level = "!"
	if level == 50: level = " CRITICAL"

	# 格式化终端输出并输出到终端
	terminal_output = f"[{level}] {content}"
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
			required_fields = ["database_data", "target_dict", "module_path", "llm_api"]
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
			"target_dict": "target.txt",
			"start_index": 0,
			"module_path": "./module/",
			"llm_api": {
				"api_key": "none",
				"base_url": "https://api.deepseek.com/v1",
			}
		}
		
		with open(config_file, 'w', encoding='utf-8') as file:
			json.dump(default_config, file, ensure_ascii=False, indent=4)
		
		log_message("config.json 重建完成")
		return True
	except Exception as e:
		log_message(f"创建配置文件失败: {str(e)}", 50)
		return False