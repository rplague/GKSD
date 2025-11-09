import multiprocessing
import sys
from tqdm import tqdm


import config_operator
import basic_program
import mariadb_operator
import qdrant_operator
from ai_modules import text_vectorization
import xml_operator

# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

'''
脚本任务：
- 将标准词汇表中所有条目的唯一向量信息导入qdrant同名集合中

'''

basic_program.log_message("正在获取 config 信息")
config_data = config_operator.get_config_data()
start_index = config_data["start_index"]
basic_program.log_message("成功获取 config 信息")

basic_program.log_message("正在获取 标准词汇表-中文 信息")
try:
	mariadb = mariadb_operator.Db_operator()
	result = mariadb.safe_db_operation(
		"SELECT id, 词语, XML含义 FROM chn_wordlist WHERE id > ?", 
		params=(start_index,), 
		fetch=True
	)
except Exception as e:
	basic_program.log_message(f"无法读取数据库信息\n{e}", 50)
	sys.exit(1)
basic_program.log_message("成功获取 标准词汇表-中文 信息")

basic_program.log_message(f"正在检测 {target_collection} 集合")
target_collection = "chn_wordlist"
qdrant = qdrant_operator.Db_operator()
if target_collection in qdrant.safe_qdrant_operation("list_collections"):
	basic_program.log_message(f"正在创建 {target_collection} 集合")
	try:
		qdrant.safe_qdrant_operation("create_collection", target_collection, )
	except Exception as e:
		basic_program.log_message(f"无法创建 {target_collection} 集合\n    {e}", 50)
		sys.exit(1)
	basic_program.log_message(f"成功创建 {target_collection} 集合")
basic_program.log_message(f"{target_collection} 集合已准备就绪")

def process_main(id_word_xml_data_tup):
	"""
	任务：
	- 从标准的xml读取向量数据
	- 组合信息创建数据点并导入数据库
	"""
	id_num, word, xml = id_word_xml_data_tup
	target_collection = "chn_wordlist"
	try:
		vector_partial = xml_operator.xml_vector_partial_retrieval(xml, "BGE_large_zh_configT01").tolist()
		
		qdrant = qdrant_operator.Db_operator()
		qdrant.create_point_struct(id_num, vector_partial)
		qdrant.safe_qdrant_operation("upsert_points", target_collection, [qdrant.create_point_struct(id_num, vector_partial)])
		basic_program.log_message(f"id 为 {id_num} 的条目已完成既定操作", printing = False)
		return True
	except Exception as e:
		basic_program.log_message(f"无法写入数据库信息\n    在处理id为{id_num}的条目时，发生了以下错误：\n{e}", 50)
		return False
basic_program.log_message("开始主任务并行……")
with multiprocessing.Pool(14) as pool:
	results = list(tqdm(pool.imap(process_main, result), total=len(result)))
basic_program.log_message("主任务已完成")