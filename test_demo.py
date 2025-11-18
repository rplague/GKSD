import sys
import traceback

import basic_program
import gksd_operator
'''
脚本任务：
- 测试新的log程序

'''


# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

GKSD_operator = gksd_operator.GKSD_operator()

# answer_list = GKSD_operator.safe_db_operation("search", name = "人工智能")

# print("搜索结果")
# for answer in answer_list:
# 	print(answer[0], "\t", answer[1], "\n")


GKSD_operator.safe_db_operation("upsert", name = "地铁")