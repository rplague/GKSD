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
	
	该函数用于验证程序运行所需的环境配置
	
	Returns:
		bool: 如果所有基本运行条件满足或可修复则返回True，否则返回False
	"""
	try:
		# 确定单位存储文件
		if not os.path.exists("config.json"):
			log_message(f"设置系统错误", 30)
			answer = input("    是否开始重建？[Y/n]")
			if answer == "n":
				log_message(f"设置系统取消重建")
				log_message(f"系统关机", 0)
				return False
			with open("config.json", 'w', encoding='utf-8') as file:
				config_data = {
								"database_data": {
									"host": "localhost",
									"user": "your_username",
									"password": "your_password",
									"database": "test_db"
								},
								"target_dict": None,
								"start_index": 0,
								"module_path": "./module/"
								}
				json.dump(config_data, file, ensure_ascii=False, indent=4)
				print("    config.json重建.....完成")
		log_message("初始化全部完成")
		return True
	except Exception as e:
		log_message(f"初始化错误 {str(e)}", 50)
		return False

	