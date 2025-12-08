import sys
from tqdm import tqdm

import config_operator
import basic_program
import gksd_operator
import logicfile_operator
import xml_operator
import ai_modules

basic_program.log_message("开始脚本任务 task05", 0)

GKSD_operator = gksd_operator.GKSD_operator()
n = 25073
for index in range(3,n):
        xml_data_list = GKSD_operator.mariadb_operator.safe_db_operation(
                "SELECT XML含义 FROM chn_wordlist WHERE id = ?",
                params=(index,),
                fetch=True
        )
        if xml_data_list:
                xml_data = xml_data_list[0][0]
        else:
                raise
        data = {
                "id": index,
                "meaning": xml_operator.xml_semantic_partial_retrieval(xml_data, "Initial_Thaw_DS"),
                "unsure_relational_list": xml_operator.xml_unsure_relational_partial_retrieval(xml_data)
        }
        answer_list = GKSD_operator.safe_db_operation("search", id_num=data["id"], with_vectors=True)
        if answer_list:
                answer = answer_list[0]
        else:
                raise
        data["word"] = answer["word"]
        data["position"] = answer["vector"]

        answer_list = GKSD_operator.safe_db_operation("search", vector=data["position"], logic_add="PartOf")
        if not answer_list:
                raise
        choice_list = []
        for answer in answer_list:
                choice_list.append(answer['word'])
        new_PartOf = {}
        new_PartOf["word"] = ai_modules.logic_PartOf(data["word"], data["meaning"], choice_list)
        if index <= 12:
                print(data["word"], data["id"], choice_list, new_PartOf["word"])
        id_list = GKSD_operator.mariadb_operator.safe_db_operation(
                "SELECT id FROM chn_wordlist WHERE 词语 = ?",
                params=(new_PartOf["word"],),
                fetch=True
        )
        if not id_list:
                print("错误的AI返回 忽略关系")
                continue
        id_num = id_list[0][0]

        xml_data = xml_operator.xml_unsure_relational_partial_adding(xml_data, "Initial_Thaw_DS", "PartOf", id_num, confidence=0.2)

        if index <= 10:
                print("\n继续则输入[qweasd]")
                if input(">>> ") != "qweasd":
                        break
        xml_data = GKSD_operator.mariadb_operator.safe_db_operation(
                "UPDATE chn_wordlist SET XML含义 = ? WHERE id = ?;",
                params=(xml_data, index,),
                fetch=False
        )
        print("\r", index, "/", str(n), end="")
