import sys
from tqdm import tqdm

import config_operator
import basic_program
import gksd_operator
import xml_operator

basic_program.log_message("开始脚本任务 task06", 0)

# 将重复自引用的错误partof删除

GKSD_operator = gksd_operator.GKSD_operator()
n = 25073
target = 0
for index in range(1,n):
		xml_data_list = GKSD_operator.mariadb_operator.safe_db_operation(
				"SELECT XML含义 FROM chn_wordlist WHERE id = ?",
				params=(index,),
				fetch=True
		)
		if xml_data_list: xml_data = xml_data_list[0][0]
		else: raise
		xml_data_check = xml_operator.xml_check(xml_data, auto=True, id_num=index)
		if xml_data_check:
			if type(xml_data_check) == str and target <= 10:
					print(index, xml_data[:200], "\n", "---" * 20, "\n", xml_data_check[-400:], xml_data[-400:])
					print("\n继续则输入[qweasd]")
					if input(">>> ") != "qweasd":
							break
			if type(xml_data_check) == str:
				xml_data = xml_data_check
				target += 1
			GKSD_operator.mariadb_operator.safe_db_operation(
					"UPDATE chn_wordlist SET XML含义 = ? WHERE id = ?;",
					params=(xml_data, index,),
					fetch=False
			)
		print("\r", index, "/", str(n), end="")
