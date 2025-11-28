import sys
from tqdm import tqdm

import config_operator
import basic_program
import gksd_operator
import xml_operator

# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

GKSD_operator = gksd_operator.GKSD_operator()

for i in tqdm(range(5, 6), desc="处理进度", unit="条"):
	answer_list = GKSD_operator.mariadb_operator.safe_db_operation(
		"SELECT XML含义 FROM chn_wordlist WHERE id = ?", 
		params=(i,),
		fetch=True
	)
	xml_data = answer_list[0][0]
	new_xml_data = xml_operator.xml_rebuild(xml_data)
	print(new_xml_data)
	print(xml_data)
	# GKSD_operator.mariadb_operator.safe_db_operation(
	# 	"UPDATE chn_wordlist SET XML含义 = ? WHERE id = ?", 
	# 	params=(new_xml_data,i,),
	# 	fetch=False
	# )
	