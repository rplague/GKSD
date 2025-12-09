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
		level = 0
		log_n = "\n    "
		log = "GKSD_operator __init__ 开始" + log_n
		try:
			self.mariadb_operator = mariadb_operator.Db_operator()
			self.qdrant_operator = qdrant_operator.Db_operator()
			log = log + "下游数据库初始化\t完成" + log_n
			try:
				self.zgbk_searcher = web_search.ZgbkSearcher()
				log = log + "搜索浏览器初始化\t完成" + log_n
			except Exception as e:
				level = 30
				log = log + "联网搜索浏览器初始化\t失败" + log_n \
					+ f"{e}" + log_n
			try:
				logicfile = logicfile_operator.LogicfileIndex("data/PartOf_data_statistics_summary.json")
				if not isinstance(logicfile, logicfile_operator.LogicfileIndex):
					raise Exception("未能获得逻辑数据")
				self.PartOf_logic_add_vector = []
				for div in range(len(logicfile)):
					self.PartOf_logic_add_vector.append(logicfile[div]["mean"])
				log = log + "预制逻辑向量初始化\t完成" + log_n
			except Exception as e:
				level = 30
				log = log + "预制逻辑向量初始化\t失败" + log_n \
					+ f"{e}" + log_n
			ai_modules.text_vectorization("测试")
			log = log + "本地模型预加载\t完成" + log_n

			if level < 20:
				level = 20
				log = log + "GKSD_operator\t初始化完成"

		except Exception as e:
			if level < 30:
				level = 50
			error_traceback = traceback.format_exc()
			log = log + f"错误类型\t{type(e).__name__}" + log_n\
				+ f"错误信息\t{str(e)}" + log_n\
				+ f"完整栈追踪:\n{error_traceback}"
			raise
		finally:
			basic_program.log_message(log, level)

	def safe_db_operation(
		self,
		operation: str,
		**kwargs) -> Optional[Any]:

		if operation == "upsert":
			# return self._upsert(**kwargs)
			raise ValueError(f"upsert 操作不安全")
		elif operation == "search":
			# return self._search(**kwargs)
			raise ValueError(f"search 操作即将被废除")
		elif operation == "search_v2":
			return self._search_v2(**kwargs)
		else:
			raise ValueError(f"operation参数错误 无 {operation} 操作")

	def _upsert(self, auto: bool = True, **kwargs) -> bool:
		# log = f"GKSD_operator 受理添加词条\n    添加内容 {name}\t添加模式 {auto}\n    "
		def _insert_to_db(word_structure: dict, target_collection: str = "chn_wordlist") -> None:
			"""
			将词语及其相关信息插入数据库
			"""
			# xml检查

			# mariadb插入
			self.mariadb_operator.safe_db_operation(
				"INSERT INTO chn_wordlist (词语, XML含义) VALUES (?, ?)",
				params=(word_structure['word'], word_structure['xml'],)
			)
			# qdrant插入
			word_structure['id'] = self.mariadb_operator.safe_db_operation(
				"SELECT id FROM chn_wordlist WHERE XML含义 = ?",
				params=(xml_data,),
				fetch=True
			)
			if not id_list:
					raise Exception(f"回溯插入id失败 词语为{word}")
			id_num = int(id_list[0][0])
			self.qdrant_operator.safe_qdrant_operation(
				"upsert_points",
				target_collection,
				[self.qdrant_operator.create_point_struct(word_structure['id'], vector)]
			)
		log = ""
		try:
			if auto == True:
				# 参数检查
				if not kwargs.get("word"):
					raise ValueError("自动添加模式参数缺失")
				word_structure = {
					"id": None,
					"word": kwargs.get("word"),
					"xml": None,
					"vector": None
				}

				# 唯一性确认
				# search_list = self._search(name=word, log_printing=False, **kwargs)	|被淘汰
				# word_list = [item["word"] for item in search_list]					|
				# if word in word_list:													|
				# 	raise ValueError("词条已存在 添加失败")							|
				# log = log + f"确认唯一性......完成\n    "								|

				# 释义获取
				# # 搜索来自中国网络百科全书的释义
				# word_meaning_zgbk = self.zgbk_searcher.search(word_structure['word'])						|被淘汰
				# # 获取结构化释义																			|
				# word_meaning_ITDS = ai_modules.unified_explain(word_structure['word'], word_meaning_zgbk)	|
				# 获取向量坐标
				word_meaning_BGE_large_zh_configT01 = ai_modules.text_vectorization(word_meaning_ITDS)
				log = log + f"词语释义数据生成完成\n    "
				# xml字符操作
				# xml_data = xml_operator.xml_semantic_partial_adding(xml_operator.generate_empty_word_definition_xml(),	|被淘汰
				# 													"www.zgbk.com",											|
				# 													word_meaning)											|
				# xml_data = xml_operator.xml_semantic_partial_adding(xml_data,												|
				# 													"Initial_Thaw_DS",										|
				# 													word_meaning_ITDS)										|
				# xml_data = xml_operator.xml_vector_partial_adding(xml_data,												|
				# 												  "BGE_large_zh_configT01",									|
				# 												  str(word_meaning_BGE_large_zh_configT01.tolist()))		|
				# log = log + f"xml生成.........完成\n    "
				_insert_to_db(word_structure)
				log = log + f"数据库操作......完成\n    "

			else:
				raise Exception("")
		except Exception as e:
			level = 40
			error_traceback = traceback.format_exc()
			err_log = f"错误类型\t{type(e).__name__}\n    错误信息\t{str(e)}\n    完整栈追踪:\n{error_traceback}"
			log = log + err_log
			basic_program.log_message(log, 30, kwargs.get("log_printing", True))
			raise
		# log = f"GKSD_operator 受理添加词条\n    添加内容 {name}\t定位释义 {word_meaning_ITDS}"
		basic_program.log_message(log, 20, kwargs.get("log_printing", True))
		return True

	def _search(self, name: Optional[str] = None, id_num: Optional[int] = None, vector: Optional[list] = None, **kwargs) -> List:
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
		def get_answer_func(id_num, **kwargs):
			result = self.mariadb_operator.safe_db_operation(
				"SELECT 词语, XML含义 FROM chn_wordlist WHERE id = ?", 
				params=(id_num,),
				fetch=True
			)
			if not result:
				raise Exception(f"mariadb_operator查询失败 ID为{id_num}")
			result = result[0]
			if not kwargs.get("with_xml", True):
				result[1] = None
			answer = {
				"id": id_num,
				"word": result[0],
				"xml": result[1],
				"score": kwargs.get("score"),
				"payload": kwargs.get("payload"),
				"vector": kwargs.get("vector")
			}
			return answer

		try:
			target_collection = "chn_wordlist"
			log = f"GKSD_operator 受理查询\n    "
			if name != None:
				log = log + f"查询内容 {name}\n    "

				vector = ai_modules.text_vectorization(name).tolist()
				answer_list = self.qdrant_operator.safe_qdrant_operation(
					"search_points",
					target_collection,
					vector,
					**kwargs
				)
				if not answer_list:
					raise Exception(f"qdrant_operator查询失败 文段为{name}")
				for index, answer in enumerate(answer_list):
					answer = get_answer_func(
						answer.id,
						score=answer.score,
						payload=answer.payload,
						vector=answer.vector,
						**kwargs
					)
					answer_list[index] = answer
				log = log + "词条查询........完成"

			elif vector != None:
				if len(vector) < 1000:
					raise Exception(f"{len(vector)}向量长度不支持")
				logic_add = kwargs.get("logic_add", None)
				if logic_add:
					if logic_add == "PartOf":
						logic_add_vector = self.PartOf_logic_add_vector
					else:
						raise Exception(f"{logic_add}逻辑类型不存在")

					vector_np = np.array(vector)
					logic_add_vector_np = np.array(logic_add_vector)
					target_vector = (vector_np + logic_add_vector_np).tolist()
					log = log + f"检测到并完成逻辑添加 {logic_add}\n    "
				else:
					target_vector = vector
				log = log + f"查询vector {target_vector[:3]}\n    "
				qdrant_answer_list = self.qdrant_operator.safe_qdrant_operation(
					"search_points",
					target_collection,
					target_vector,
					with_vectors=True,
					**kwargs
				)
				if not qdrant_answer_list:
					raise Exception(f"qdrant_operator查询失败 文段为{name}")
				answer_list = []
				for answer in qdrant_answer_list:
					if answer.vector != vector:
						answer = get_answer_func(
							answer.id,
							score=answer.score,
							payload=answer.payload,
							vector=answer.vector,
							**kwargs
						)
						answer_list.append(answer)

				log = log + "词条查询........完成"
			elif id_num != None:
				log = log + f"查询条目ID {id_num}\n    "
				answer = get_answer_func(
					id_num,
					**kwargs
				)
				log = log + f"mariadb_operator查询完成\n    "
				qdrant_answer_list = self.qdrant_operator.safe_qdrant_operation(
					"retrieve_points",
					target_collection,
					[int(id_num)],
					**kwargs
				)
				if qdrant_answer_list:
					qdrant_answer = qdrant_answer_list[0]
				else:
					raise Exception(f"qdrant_operator查询失败 id为{id_num}")
				answer["payload"] = qdrant_answer.payload
				answer["vector"] = qdrant_answer.vector
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

	def _search_v2(self, id_num: Optional[str] = None, text: Optional[str] = None, vector: Optional[list] = None, logic_ask: Optional[list] = None, **kwargs) -> List:
		"""
		汉语词典查询功能重构版

		"""
		def get_answer_func(id_num, **kwargs):
			result = self.mariadb_operator.safe_db_operation(
				"SELECT 词语, XML含义 FROM chn_wordlist WHERE id = ?", 
				params=(id_num,),
				fetch=True
			)
			if not result:
				raise Exception(f"mariadb_operator查询失败 ID为{id_num}")
			result = result[0]
			word = result[0]
			xml = result[1]
			vector = xml_operator.xml_vector_partial_retrieval(xml, "BGE_large_zh_configT01")
			if not kwargs.get("with_xml", True):
				result[1] = None
			answer = {
				"id": id_num,
				"word": word,
				"xml": xml,
				"score": kwargs.get("score"),
				"payload": kwargs.get("payload"),
				"vector": vector
			}
			return answer
		level = 20
		log_n = "\n    "
		log = "_search_v2 开始" + log_n
		input_var = f"参数" + log_n \
			+ f"id_num\t{id_num}" + log_n \
			+ f"text\t{text}" + log_n
		log = log + input_var

		# 主函数模块
		try:
			if id_num != None:
				log = log + "基于ID搜索" + log_n
				answer = get_answer_func(
					id_num
				)
				answer_list = [answer]
				if logic_ask:
					log = log + "开始位移" + log_n
					logic_vector_type = logic_ask['logic_vector']
					logic_calc_method = logic_ask['calculation_method']

					if not logic_vector_type or not logic_calc_method:
						raise Exception(f"logic_ask缺少参数却被激活")

					input_var = input_var + f"logic_ask\t{logic_ask}" + log_n
					log = log + input_var
					if logic_vector_type == "PartOf":
						logic_vector = self.PartOf_logic_add_vector
					else:
						raise Exception(f"{logic_vector_type}逻辑类型不存在")

					set_vector = np.array(answer['vector'])
					logic_vector = np.array(logic_vector)
					if logic_calc_method == "+":
						target_vector = (set_vector + logic_vector).tolist()
					elif logic_calc_method == "-":
						target_vector = (set_vector - logic_vector).tolist()
					else:
						raise Exception(f"{logic_calc_method} 逻辑运算不存在")
					answer_list = self._search_v2(vector=target_vector)

				log = log + "查询\t完成" + log_n

			elif text != None:
				log = log + "基于输入字符搜索" + log_n
				target_collection = "chn_wordlist"
				text_vector = ai_modules.text_vectorization(text).tolist()

				answer_list = self.qdrant_operator.safe_qdrant_operation(
					"search_points",
					target_collection,
					text_vector,
					**kwargs
				)
				if not answer_list:
					raise Exception('qdrant_operator 没有返回查询结果')
				for index, answer in enumerate(answer_list):
					answer = get_answer_func(
						answer.id,
						score=answer.score,
						payload=answer.payload,
						vector=answer.vector,
						**kwargs
					)
					answer_list[index] = answer
				log = log + "查询\t完成" + log_n

			elif vector != None:
				log = log + "基于向量坐标搜索" + log_n

				if logic_ask:
					log = log + "开始位移" + log_n
					logic_vector_type = logic_ask['logic_vector']
					logic_calc_method = logic_ask['calculation_method']

					if not logic_vector_type or not logic_calc_method:
						raise Exception(f"logic_ask缺少参数却被激活")

					input_var = input_var + f"logic_ask\t{logic_ask}" + log_n
					log = log + input_var
					if logic_vector_type == "PartOf":
						logic_vector = self.PartOf_logic_add_vector
					else:
						raise Exception(f"{logic_vector_type}逻辑类型不存在")

					set_vector = np.array(vector)
					logic_vector = np.array(logic_vector)
					if logic_calc_method == "+":
						target_vector = (set_vector + logic_vector).tolist()
					elif logic_calc_method == "-":
						target_vector = (set_vector - logic_vector).tolist()
					else:
						raise Exception(f"{logic_calc_method} 逻辑运算不存在")
					answer_list = self._search_v2(vector=target_vector)
				else:
					target_collection = "chn_wordlist"
					answer_list = self.qdrant_operator.safe_qdrant_operation(
						"search_points",
						target_collection,
						vector,
						**kwargs
					)
					if not answer_list:
						raise Exception('qdrant_operator 没有返回查询结果')
					for index, answer in enumerate(answer_list):
						answer = get_answer_func(
							answer.id,
							score=answer.score,
							payload=answer.payload,
							vector=answer.vector,
							**kwargs
						)
						answer_list[index] = answer
				log = log + "查询\t完成" + log_n

			else:
				raise Exception('参数缺失')
			log = f"_search_v2 运行成功" + log_n \
				+ input_var
			return answer_list
		except Exception as e:
			level = 50
			error_traceback = traceback.format_exc()
			log = log + f"错误类型\t{type(e).__name__}" + log_n\
				+ f"错误信息\t{str(e)}" + log_n\
				+ f"完整栈追踪:\n{error_traceback}"
			raise
		finally:
			basic_program.log_message(log, level, kwargs.get("log_printing", True))
	