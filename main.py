import multiprocessing
import sys
from tqdm import tqdm
import traceback
import json
import numpy as np

import config_operator
import basic_program
import ai_modules

# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

'''
脚本任务：
- 遍历标准词汇表，并半自动判断其对应partof名称。
- 查询partof名称，若词汇表中缺失则自动添加。
- 若成功查询partof则计算partof的向量相对位置，并将差值计算并统计。
- 求出所有有效三元组的向量平均差距。
- 反向验证有效性。
'''


config_data = config_operator.get_config_data()
index = config_data["index"]

def process_main(index_for_now):
	"""
	任务：
	- 对于特定索引的条目半自动判断其对应父类名称
	- 查询父类名称，若词汇表中缺失则自动添加
	- 在此基础上将差值计算和三元组一同统计
	"""
	level = 50
	import gksd_operator
	target_collection = "chn_wordlist"
	try:
		GKSD_operator = gksd_operator.GKSD_operator()
		word = GKSD_operator.safe_db_operation("search", id_num = index_for_now)[0][0]
		master_word = ai_modules.logic_PartOf(word)
		if master_word == ">无结果<" :
			level = 20
			raise Exception("未找到有效partof结果")
		search_list = GKSD_operator.safe_db_operation("search", name = master_word)
		search_list = [answer[0] for answer in search_list]
		if master_word not in search_list:
			answer = GKSD_operator.safe_db_operation("upsert", name = master_word)
			if not answer:
				level = 30
				raise Exception("未能成功添加partof")

		id_list = GKSD_operator.mariadb_operator.safe_db_operation(
			"SELECT id FROM chn_wordlist WHERE 词语 = ?",
			params = (word,),
			fetch = True
		)
		id_list = [item[0] for item in id_list] if id_list else []

		master_id_list = GKSD_operator.mariadb_operator.safe_db_operation(
			"SELECT id FROM chn_wordlist WHERE 词语 = ?",
			params = (master_word,),
			fetch = True
		)
		master_id_list = [item[0] for item in master_id_list] if master_id_list else []

		vector = GKSD_operator.qdrant_operator.safe_qdrant_operation(
			"retrieve_points",
			target_collection,
			id_list,
			with_payload = False,
			with_vectors = True
		)[0].vector
		master_vector = GKSD_operator.qdrant_operator.safe_qdrant_operation(
			"retrieve_points",
			target_collection,
			master_id_list,
			with_payload = False,
			with_vectors = True
		)[0].vector

		PartOf_vector = np.array(master_vector) - np.array(vector)
		if isinstance(PartOf_vector, np.ndarray):
			PartOf_vector = PartOf_vector.tolist()

		data = {
			"word_id": id_list[0] if id_list else None,
			"master_id": master_id_list[0] if master_id_list else None,
			"vector": PartOf_vector
		}

		with open('PartOf.json', 'a', encoding='utf-8') as file:
			file.write(json.dumps(data) + '\n')  # 每行一个JSON对象
		basic_program.log_message(
			f"    id {index_for_now} 处理完成"
		)
	except Exception as e:
		if level > 30:
			error_traceback = traceback.format_exc()
			basic_program.log_message(
				f"    在处理id为{index_for_now}的条目时，发生了以下错误：\n"
				f"    错误类型: {type(e).__name__}\n"
				f"    错误信息: {str(e)}\n"
				f"    完整栈追踪:\n{error_traceback}", 
				level
			)
		else:
			basic_program.log_message(
				f"    在处理id为{index_for_now}的条目时，发生了以下错误：\n"
				f"    {e}\n", 
				level
			)
	finally:
		GKSD_operator.zgbk_searcher.close()
		return True

basic_program.log_message("开始主任务并行……")
with multiprocessing.Pool(15) as pool:
	results = list(tqdm(pool.imap(process_main, range(208, index + 1)), total = index))
basic_program.log_message("主任务已完成")