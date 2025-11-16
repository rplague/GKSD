import sys
import traceback

import basic_program

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


basic_program.log_message("重要信息测试",0)
basic_program.log_message("debug信息测试",10)
basic_program.log_message("普通信息测试",20)
basic_program.log_message("警告信息测试",30)
basic_program.log_message("错误信息测试",40)
basic_program.log_message("严重错误信息测试",50)
