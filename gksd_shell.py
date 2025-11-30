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
now_position = None

while True:
	command = input("\n>>> ").split(" ")
	if command[0] == "search":
		if len(command) == 3:
			if command[1] == "+":
				if command[2] == "PartOf":
					answer_list = GKSD_operator.safe_db_operation("search", vector=now_position, logic_add="PartOf")
				else:
					print(f"    错误逻辑指令 {command[2]}")
		elif len(command) == 2:
			answer_list = GKSD_operator.safe_db_operation("search", name=command[1])
		for answer in answer_list:
			print(f"{answer["id"]}\t{answer["word"]}\n{answer["score"]}")
	elif command[0] == "set":
		answer_list = GKSD_operator.safe_db_operation("search", id_num=int(command[1]), with_vectors=True)
		print("    已定位至：")
		for answer in answer_list:
			print(f"{answer["id"]}\t{answer["word"]}")
		now_position = answer["vector"]
	elif command[0] == "exit":
		print("    bye")
		break
