from typing import List, Tuple, Any, Optional, Union, Dict
import traceback
import numpy as np

import basic_program
import ai_modules
import mariadb_operator
import qdrant_operator
import xml_operator
import logicfile_operator
from server import web_search

class GKSD_operator(object):
	def __init__(self):
		log = "GKSD_operator 初始化\n    "
		try:
			level = 20
			self.mariadb_operator = mariadb_operator.Db_operator()
			self.qdrant_operator = qdrant_operator.Db_operator()
			log = log + "下游数据库\t\t初始化完成\n    "
			self.zgbk_searcher = web_search.ZgbkSearcher()
			log = log + "联网搜索浏览器\t初始化完成\n    "
			logicfile = logicfile_operator.LogicfileIndex("data/PartOf_data_statistics_summary.json")
			self.PartOf_logic_add_vector = []
			for div in range(len(logicfile)):
				self.PartOf_logic_add_vector.append(logicfile[div]["mean"])
			log = log +"预制逻辑向量\t初始化完成\n    "
			ai_modules.text_vectorization("测试")
			log = log +"本地模型预加载\t初始化完成\n    "
			log = log + "GKSD_operator\t初始化完成"

		except Exception as e:
			level = 50
			error_traceback = traceback.format_exc()
			err_log = f"    错误类型\t{type(e).__name__}\n    错误信息\t{str(e)}\n    完整栈追踪:\n{error_traceback}"
			log = log + "GKSD_operator\t初始化失败\n详细信息：\n\n" + err_log
		finally:
			basic_program.log_message(log, level)

	def safe_db_operation(self,
						  operation: str,
						  **kwargs) -> Optional[Any]:

		if operation == "upsert":
			return self._upsert(**kwargs)
		elif operation == "search":
			return self._search(**kwargs)
		else:
			raise ValueError(f"operation参数错误 无 {operation} 操作")

	def _upsert(self,
				name: str,
				auto: bool = True,
				**kwargs) -> bool:
		log = f"GKSD_operator 受理添加词条\n    添加内容 {name}\t添加模式 {auto}\n    "
		try:
			if auto == True:
				search_list = self._search(name=name, log_printing=False, **kwargs)
				word_list = [item["word"] for item in search_list]
				if name in word_list:
					raise ValueError("词条已存在 添加失败")
				log = log + f"确认唯一性......完成\n    "
				# 搜索来自中国网络百科全书的释义
				word_meaning = self.zgbk_searcher.search(name)
				# 获取结构化释义
				word_meaning_ITDS = ai_modules.unified_explain(name, word_meaning)
				# 获取向量坐标
				word_meaning_BGE_large_zh_configT01 = ai_modules.text_vectorization(word_meaning_ITDS)
				log = log + f"词语释义数据生成完成\n    "
				# xml字符操作
				xml_data = xml_operator.xml_semantic_partial_adding(xml_operator.generate_empty_word_definition_xml(),
																	"www.zgbk.com",
																	word_meaning)
				xml_data = xml_operator.xml_semantic_partial_adding(xml_data,
																	"Initial_Thaw_DS",
																	word_meaning_ITDS)
				xml_data = xml_operator.xml_vector_partial_adding(xml_data,
																  "BGE_large_zh_configT01",
																  str(word_meaning_BGE_large_zh_configT01.tolist()))
				# log = log + f"xml生成.........完成\n    "
				# mariadb插入
				self.mariadb_operator.safe_db_operation(
					"INSERT INTO chn_wordlist (词语, XML含义) VALUES (?, ?)",
					params=(name, xml_data,)
				)
				# log = log + f"mariadb操作.....完成\n    "
				# qdrant插入
				id_list = self.mariadb_operator.safe_db_operation(
					"SELECT id FROM chn_wordlist WHERE 词语 = ?",
					params=(name,),
					fetch=True
				)
				id_num = id_list[0][0]
				target_collection = "chn_wordlist"

				self.qdrant_operator.safe_qdrant_operation(
					"upsert_points",
					target_collection,
					[self.qdrant_operator.create_point_struct(int(id_num),
					 word_meaning_BGE_large_zh_configT01.tolist())]
				)
				log = log + f"数据库操作......完成\n    "

			else:
				search_list = self._search(name=name, log_printing=False, **kwargs)
				word_list = [item["word"] for item in search_list]
				if name in word_list: raise ValueError("词条已存在 添加失败")
				log = log + f"确认唯一性......完成\n    "

				word_meaning = kwargs.get("word_meaning")
				if word_meaning == None: raise ValueError("参数缺失 未输入定位释义")
				word_meaning_ITDS = ai_modules.unified_explain(name, word_meaning)
				word_meaning_BGE_large_zh_configT01 = ai_modules.text_vectorization(word_meaning_ITDS)
				log = log + f"词语释义数据生成完成\n    "

				# xml字符操作
				word_meaning_source = kwargs.get("word_meaning_source", "admin_input")
				xml_data = xml_operator.xml_semantic_partial_adding(xml_operator.generate_empty_word_definition_xml(),
																	word_meaning_source,
																	word_meaning)
				xml_data = xml_operator.xml_semantic_partial_adding(xml_data,
																	"Initial_Thaw_DS",
																	word_meaning_ITDS)
				xml_data = xml_operator.xml_vector_partial_adding(xml_data,
																  "BGE_large_zh_configT01",
																  str(word_meaning_BGE_large_zh_configT01.tolist()))
				# mariadb插入
				self.mariadb_operator.safe_db_operation(
					"INSERT INTO chn_wordlist (词语, XML含义) VALUES (?, ?)",
					params=(name, xml_data,)
				)
				# qdrant插入
				id_list = self.mariadb_operator.safe_db_operation(
					"SELECT id FROM chn_wordlist WHERE XML含义 = ?",
					params=(xml_data,),
					fetch=True
				)
				id_num = id_list[0][0]
				target_collection = "chn_wordlist"
				self.qdrant_operator.safe_qdrant_operation(
					"upsert_points",
					target_collection,
					[self.qdrant_operator.create_point_struct(int(id_num),
					 word_meaning_BGE_large_zh_configT01.tolist())]
				)
				log = log + f"数据库操作......完成\n    "
		except Exception as e:
			level = 40
			error_traceback = traceback.format_exc()
			err_log = f"错误类型\t{type(e).__name__}\n    错误信息\t{str(e)}\n    完整栈追踪:\n{error_traceback}"
			log = log + err_log
			basic_program.log_message(log, 30, kwargs.get("log_printing", True))
			raise
		log = f"GKSD_operator 受理添加词条\n    添加内容 {name}\t定位释义 {word_meaning_ITDS}"
		basic_program.log_message(log, 20, kwargs.get("log_printing", True))
		return True

	def _search(self,
				name: str = None,
				id_num: int = None,
				vector: int = None,
				**kwargs) -> List:
		"""
		汉语词典查询功能

		支持两种查询模式：
		1. 语义查询：当仅提供name参数时，使用BGE向量模型将查询文本转换为向量表示，
			在Qdrant向量数据库中进行相似度搜索，返回语义相关的词语列表
		2. 精确查询：当提供id_num参数时，直接在MySQL数据库中按ID查询特定词条

		参数:
			name (str): 查询文本，支持任意长度的中文文本（语义查询模式使用）
			vector
			id_num (int): 词条ID，用于精确查询特定词条
			**kwargs: 
				Qdrant搜索的可选参数	用于自定义搜索行为（仅语义查询模式有效）
				log_printing			log系统输出控制

		返回:
			list: 包含查询结果的字典列表，每个字典包含：
				- id: 词条ID
				- word: 词语
				- meaning: 含义
				- score: 相似度分数（仅语义查询）
				- payload: 向量数据库中的payload
				- vector: 向量表示

		报错:
			FileNotFoundError: BGE模型文件不存在
			ConnectionError: 数据库连接失败
			ValueError: 输入参数格式错误
			Exception: 其他处理过程中的异常

		注意:
			- 当id_num为None时，执行语义查询，返回语义相关而非精确匹配的结果
			- 当id_num提供时，执行精确查询，忽略name参数的语义内容
			- 查询过程涉及多个系统组件，性能受网络和硬件资源影响
			- 语义查询返回结果数量受Qdrant配置和score_threshold参数限制
			- XML解析依赖特定的语义标签结构"Initial_Thaw_DS"
		"""
		try:
			target_collection = "chn_wordlist"
			log = f"GKSD_operator 受理查询\n    "
			if name != None:
				log = log + f"查询内容 {name}\n    "

				vector_partial = ai_modules.text_vectorization(name).tolist()
				answer_list = self.qdrant_operator.safe_qdrant_operation("search_points",
																		 target_collection,
																		 vector_partial,
																		 with_payload = True,
																		 with_vectors = True,
																		 **kwargs)
				log = log + "向量查询........完成\n    "
				for index, answer in enumerate(answer_list):
					result = self.mariadb_operator.safe_db_operation(
						"SELECT 词语, XML含义 FROM chn_wordlist WHERE id = ?", 
						params=(answer.id,),
						fetch=True
					)
					result = result[0]
					meaning = xml_operator.xml_semantic_partial_retrieval(result[1], "Initial_Thaw_DS")
					answer = {
						"id": answer.id,
						"word": result[0],
						"meaning": meaning,
						"score": answer.score,
						"payload": answer.payload,
						"vector": answer.vector
					}
					answer_list[index] = answer
				log = log + "词条查询........完成"
			elif vector != None:
				logic_add = kwargs.get("logic_add", None)
				if logic_add:
					if logic_add == "PartOf":
						logic_add_vector = self.PartOf_logic_add_vector
					vector_np = np.array(vector)
					logic_add_vector_np = np.array(logic_add_vector)
					vector = (vector_np + logic_add_vector_np).tolist()
					log = log + f"检测到并完成逻辑添加 {logic_add}\n    "
				log = log + f"查询vector {vector[:3]}\n    "
				answer_list = self.qdrant_operator.safe_qdrant_operation("search_points",
																		 target_collection,
																		 vector,
																		 with_payload = True,
																		 with_vectors = True,
																		 **kwargs)
				log = log + "向量查询........完成\n    "
				for index, answer in enumerate(answer_list):
					result = self.mariadb_operator.safe_db_operation(
						"SELECT 词语, XML含义 FROM chn_wordlist WHERE id = ?", 
						params=(answer.id,),
						fetch=True
					)
					result = result[0]
					meaning = xml_operator.xml_semantic_partial_retrieval(result[1], "Initial_Thaw_DS")
					answer = {
						"id": answer.id,
						"word": result[0],
						"meaning": meaning,
						"score": answer.score,
						"payload": answer.payload,
						"vector": answer.vector
					}
					answer_list[index] = answer
				log = log + "词条查询........完成"
			elif id_num != None:
				log = log + f"查询条目ID {id_num}\n    "
				result = self.mariadb_operator.safe_db_operation(
					"SELECT id, 词语, XML含义 FROM chn_wordlist WHERE id = ?", 
					params=(id_num,),
					fetch=True
				)
				result = result[0]
				meaning = xml_operator.xml_semantic_partial_retrieval(result[-1], "Initial_Thaw_DS")
				answer_list = self.qdrant_operator.safe_qdrant_operation("retrieve_points",
																		 target_collection,
																		 [result[0]],
																		 with_payload = True,
																		 with_vectors = True)
				answer = answer_list[0]
				answer = {
					"id": answer.id,
					"word": result[1],
					"meaning": meaning,
					"score": 1.0,
					"payload": answer.payload,
					"vector": answer.vector
				}
				answer_list = [answer]
				log = log + "词条查询........完成"
		except Exception as e:
			error_traceback = traceback.format_exc()
			err_log = f"    错误类型\t{type(e).__name__}\n    错误信息\t{str(e)}\n    完整栈追踪:\n{error_traceback}"
			log = log + "查询任务失败\n详细信息：\n" + err_log
			basic_program.log_message(log, 30, kwargs.get("log_printing", True))
			raise

		log = f"GKSD_operator 受理查询\n    返回 {len(answer_list)} 条结果"
		basic_program.log_message(log, 20, kwargs.get("log_printing", True))
		return answer_list
