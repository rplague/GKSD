import config_operator
import basic_program
import gksd_operator

# 初始化
situation = basic_program.boot()
if not situation:
	sys.exit(1)
situation = basic_program.init_program()
if not situation:
	sys.exit(1)

GKSD_operator = gksd_operator.GKSD_operator()
now_id = None

while True:
	command = input("\n>>> ").split(" ")
	if command[0] == "search":
		if len(command) == 3:
			if command[1] == "+":
				if command[2] == "PartOf":
					answer_list = GKSD_operator.safe_db_operation("search_v2", id_num=now_id, logic_ask={'logic_vector':"PartOf", 'calculation_method':"+"}, log_printing=False)
				else:
					print(f"    错误逻辑指令 {command[2]}")
		elif len(command) == 2:
			answer_list = GKSD_operator.safe_db_operation("search_v2", text=command[1], log_printing=False)
		for answer in answer_list:
			print(f"{answer["id"]}\t{answer["word"]}\n{answer["score"]}")
	elif command[0] == "set":
		answer_list = GKSD_operator.safe_db_operation("search_v2", id_num=int(command[1]), log_printing=False)
		answer = answer_list[0]
		now_id = answer["id"]
		print("    已定位至：", answer['word'])
		
	elif command[0] == "exit":
		print("    bye")
		break
