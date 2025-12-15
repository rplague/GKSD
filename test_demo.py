import sys

import basic_program
import gksd_operator
import xml_operator
import ai_modules

basic_program.log_message("开始脚本任务 task07", 0)

# 通过新的算法从新添加partof，增加待确认partof数量为之后逻辑推导建立基础

GKSD_operator = gksd_operator.GKSD_operator()
n = 25073
target = 0
for target_index in range(1,n):
	word_data_list = GKSD_operator.safe_db_operation("search", id_num=target_index)
	if word_data_list: word_data = word_data_list[0]
	else: raise
	GKSD_operator.advance_db_operation("auto_search_partof", word_data=word_data)
	print("\r", target_index, "/", str(n), end="")
