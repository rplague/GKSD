import sys
import traceback

import basic_program
import ai_modules
import xml_operator
import config_operator
import qdrant_operator
import mariadb_operator
'''
脚本任务：
- 输入关键词进行向量检索并将最接近的内容返回

'''


# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

config_data = config_operator.get_config_data()
basic_program.log_message(f"查询测试脚本就绪 等待用户输入关键词", printing = False)
print("    请输入查询关键词")
ask_str = str(input(">>> "))
basic_program.log_message(f"开始查询 {ask_str}", printing = False)

try:
	vector_partial = ai_modules.text_vectorization(ask_str).tolist()
except Exception as e:
	error_traceback = traceback.format_exc()
	basic_program.log_message(
		f"向量映射错误\n"
		f"    错误类型: {type(e).__name__}\n"
		f"    错误信息: {str(e)}\n"
		f"    完整栈追踪:\n{error_traceback}", 
		50
	)
	sys.exit(1)

try:
	target_collection = "chn_wordlist"
	qdrant = qdrant_operator.Db_operator()
	answer_list = qdrant.safe_qdrant_operation("search_points", target_collection, vector_partial, with_payload = False)

except Exception as e:
	error_traceback = traceback.format_exc()
	basic_program.log_message(
		f"向量数据库操作错误\n"
		f"    错误类型: {type(e).__name__}\n"
		f"    错误信息: {str(e)}\n"
		f"    完整栈追踪:\n{error_traceback}", 
		50
	)
	sys.exit(1)


try:
	mariadb = mariadb_operator.Db_operator()
	end_answer_list = []
	for answer in answer_list:
		result = mariadb.safe_db_operation(
			"SELECT XML含义 FROM chn_wordlist WHERE id = ?", 
			params=(answer.id,), 
			fetch=True
		)
		result = xml_operator.xml_semantic_partial_retrieval(result[0][0], "Initial_Thaw_DS")
		end_answer_list.append(result)
except Exception as e:
	error_traceback = traceback.format_exc()
	basic_program.log_message(
		f"标准数据库操作错误\n"
		f"    错误类型: {type(e).__name__}\n"
		f"    错误信息: {str(e)}\n"
		f"    完整栈追踪:\n{error_traceback}",
		50
	)
	sys.exit(1)

basic_program.log_message(f"查询完成")
index = 0
for index in range(10):
	print(answer_list[index],"\n",end_answer_list[index])
