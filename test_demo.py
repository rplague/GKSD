import sys
from tqdm import tqdm

import config_operator
import basic_program
import gksd_operator
import logicfile_operator
import xml_operator

basic_program.log_message("开始脚本任务 task04", 0)

GKSD_operator = gksd_operator.GKSD_operator()

logicfile_set = logicfile_operator.LogicfileSetIndex("data/PartOf.json")
for index in range(len(logicfile_set)):
	item = logicfile_set[index]
	xml_data = GKSD_operator.mariadb_operator.safe_db_operation(
		"SELECT XML含义 FROM chn_wordlist WHERE id = ?",
		params=(item["word_id"],),
		fetch=True
	)[0][0]
	xml_data = xml_operator.xml_unsure_relational_partial_adding(xml_data, "Initial_Thaw_DS", "PartOf", item["master_id"], confidence=0.2)
	if index == 0:
		print(xml_data, "\n继续则输入[qweasd]")
		if input(">>> ") != "qweasd":
			break
	xml_data = GKSD_operator.mariadb_operator.safe_db_operation(
		"UPDATE chn_wordlist SET XML含义 = ? WHERE id = ?;",
		params=(xml_data, item["word_id"],),
		fetch=False
	)
	print("\r", index, "/", len(logicfile_set), end="")
