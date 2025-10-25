import json
import basic_program

def get_config_data():
	basic_program.log_message("读取设置数据", printing = False)
	with open('config.json', 'r', encoding='utf-8') as config_file:
		config_data = json.load(config_file)
	return config_data