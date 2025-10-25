import multiprocessing
import sys
from tqdm import tqdm


import config_operator
import basic_program
from mariadb_operator import Db_operater
from ai_modules import unified_explain
import xml_operator

# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)
basic_program.log_message("正在获取 config 信息")
config_data = config_operator.get_config_data()
start_index = config_data["start_index"]
basic_program.log_message("成功获取 config 信息")

basic_program.log_message("正在获取 标准词汇表-中文 信息")
try:
	mariadb = Db_operater()
	result = mariadb.safe_db_operation(
		"SELECT id, 词语, XML含义 FROM chn_wordlist WHERE id > ?", 
		params=(start_index,), 
		fetch=True
	)
except Exception as e:
	basic_program.log_message(f"无法读取数据库信息\n{e}", 50)
	sys.exit(1)
basic_program.log_message("成功获取 标准词汇表-中文 信息")

def process_main(id_word_xml_data_tup):
	"""任务：
		- 将xml标准化为新的格式
		- 从标准的xml读取来自百科的释义并通过初融格式化
		- 结合格式化的释义生成新的有效xml并存储到数据库"""
	id_num, word, xml = id_word_xml_data_tup

	xml = xml_operator.test_operation_001(xml)

	data_text = xml_operator.test_operation_002_0(xml)

	explain_text = unified_explain(word, data_text)

	new_xml = xml_operator.test_operation_002_1(xml, "Initial_Thaw_DS", explain_text)

	try:
		mariadb = Db_operater()
		result = mariadb.safe_db_operation(
				"UPDATE chn_wordlist SET XML含义 = ? WHERE id = ?", 
				params=(new_xml, id_num)
			)
		basic_program.log_message(f"id 为 {id_num} 的条目已完成既定操作", printing = False)
		return True
	except Exception as e:
		basic_program.log_message(f"无法写入数据库信息\n    在处理id为{id_num}的条目时，发生了以下错误：\n{e}", 50)
		sys.exit(1)
basic_program.log_message("开始主任务并行……")
with multiprocessing.Pool(14) as pool:
	results = list(tqdm(pool.imap(process_main, result), total=len(result)))
basic_program.log_message("主任务已完成")