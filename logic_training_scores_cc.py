import sys
from tqdm import tqdm
import traceback
import numpy as np

import config_operator
import basic_program
import gksd_operator
import logicfile_operator

# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

GKSD_operator = gksd_operator.GKSD_operator()

logicfile_set = logicfile_operator.LogicfileSetIndex("data/PartOf.json")
now_position = None

logicfile = logicfile_operator.LogicfileIndex("data/PartOf_data_statistics_summary.json")
delta_v = []
for div in range(len(logicfile)):
	delta_v.append(logicfile[div]["mean"])
print("待测试向量差装载完成")
succes_num = 0
for data_set_index in tqdm(range(logicfile_set.get_vector_info()[0]), desc="处理数据集"):
	data_set = logicfile_set[data_set_index]
	if not data_set:
		raise
	target_id = data_set["word_id"]
	answer_id = data_set["master_id"]
	target = GKSD_operator.safe_db_operation("search", id_num=target_id, with_vectors=True, log_printing=False)
	if target:
		target = target[0]
	else:
		raise
	vector_np = np.array(target["vector"])
	delta_np = np.array(delta_v)
	answer_vector = (vector_np + delta_np).tolist()
	answer_list = GKSD_operator.safe_db_operation("search", vector=answer_vector, log_printing=False, limit=10)
	if answer_id in [answer["id"] for answer in answer_list]:
		succes_num += 1
point = (succes_num / len(logicfile_set)) * 100
print("运算完毕 Top10\n成功率 ", point, "%")

succes_num = 0
for data_set_index in tqdm(range(logicfile_set.get_vector_info()[0]), desc="处理数据集"):
	data_set = logicfile_set[data_set_index]
	if not data_set:
		raise
	target_id = data_set["word_id"]
	answer_id = data_set["master_id"]
	target = GKSD_operator.safe_db_operation("search", id_num=target_id, with_vectors=True, log_printing=False)
	if target:
		target = target[0]
	else:
		raise
	vector_np = np.array(target["vector"])
	delta_np = np.array(delta_v)
	answer_vector = (vector_np + delta_np).tolist()
	answer_list = GKSD_operator.safe_db_operation("search", vector=answer_vector, log_printing=False, limit=80)
	if answer_id in [answer["id"] for answer in answer_list]:
		succes_num += 1
point = (succes_num / len(logicfile_set)) * 100
print("运算完毕 Top80\n成功率 ", point, "%")