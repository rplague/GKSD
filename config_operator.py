import json
import traceback

import basic_program

def get_config_data():
	with open('config.json', 'r', encoding='utf-8') as config_file:
		config_data = json.load(config_file)
	return config_data

def set_config_data(path_tuple: tuple, content: str, create_missing: bool = False, **kwargs) -> None:
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
		raise ValueError("path_tuple 路径元组不能为空\n函数 set_config_data 调用失败")
	
	config_data = get_config_data()
	current = config_data
	# 遍历到倒数第二个元素
	for i, key in enumerate(path_tuple[:-1]):
		if key not in current:
			if create_missing:
				current[key] = {}
			else:
				raise ValueError(f"path_tuple 路径 '{'.'.join(path_tuple[:i+1])}' 不存在\n函数 set_config_data 调用失败")

		if not isinstance(current[key], dict):
			if create_missing:
				current[key] = {}
			else:
				raise ValueError(f"path_tuple 路径 '{'.'.join(path_tuple[:i+1])}' 不是字典类型\n函数 set_config_data 调用失败")

		current = current[key]
	last_key = path_tuple[-1]
	current[last_key] = content

	level = 0
	log_n = "\n    "
	log = "set_config_data 开始" + log_n
	input_var = f"参数" + log_n \
		+ f"path_tuple\t{path_tuple}" + log_n \
		+ f"content\t{content}" + log_n \
		+ f"create_missing\t{create_missing}"
	try:
		with open('config.json', 'w', encoding='utf-8') as config_file:
			json.dump(config_data, config_file, indent=4, ensure_ascii=False)
		log = log + f"{'.'.join(path_tuple)} 修改设置为:\n    {content}" + log_n
		if level < 20:
			level = 20
		log = f"function_name 运行成功" + log_n \
			+ input_var
	except Exception as e:
		if level < 30:
			level = 50
		error_traceback = traceback.format_exc()
		log = log + f"错误类型\t{type(e).__name__}" + log_n\
			+ f"错误信息\t{str(e)}" + log_n\
			+ f"完整栈追踪:\n{error_traceback}"
		raise
	finally:
		basic_program.log_message(
			f"set_config_data 函数执行完成\n    {'.'.join(path_tuple)} 修改设置为:\n    {content}",
			level,
			kwargs.get("log_printing", False)
		)
