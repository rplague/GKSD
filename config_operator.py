import json
import basic_program

def get_config_data():
	with open('config.json', 'r', encoding='utf-8') as config_file:
		config_data = json.load(config_file)
	return config_data

def set_config_data(path_tuple, content, create_missing=False):
	""" 
	设定设置内容
	
	输入特定条目，修改特定条目的设置内容 
	
	参数:
		path_tuple (tuple): 给予需要修改的条目的路径元组
		content (str): 替换的内容
	
	报错:
		ValueError: 路径元组为空
		KeyError: 路径不存在
		TypeError: 路径不是字典类型

	示例:
		none

	注意:
		- path_tuple 输入只支持单个路径的顺序列表
	"""
	# 输入验证
	if not path_tuple:
		raise ValueError("path_tuple 路径元组不能为空")
	
	config_data = get_config_data()
	current = config_data
	# 遍历到倒数第二个元素
	for i, key in enumerate(path_tuple[:-1]):
		if key not in current:
			if create_missing:
				current[key] = {}
			else:
				raise KeyError(f"路径 '{'.'.join(path_tuple[:i+1])}' 不存在")

		if not isinstance(current[key], dict):
			if create_missing:
				current[key] = {}
			else:
				raise TypeError(f"路径 '{'.'.join(path_tuple[:i+1])}' 不是字典类型")

		current = current[key]
	last_key = path_tuple[-1]
	current[last_key] = content


	basic_program.log_message(
		f"set_config_data 函数开始执行\n    {'.'.join(path_tuple)} 修改设置为:\n    {content}",
		printing = False
	)
	with open('config.json', 'w', encoding='utf-8') as config_file:
		json.dump(config_data, config_file, indent=4, ensure_ascii=False)
	
	basic_program.log_message(
		f"set_config_data 函数执行完成\n    {'.'.join(path_tuple)} 修改设置为:\n    {content}", 
		printing = True
	)
