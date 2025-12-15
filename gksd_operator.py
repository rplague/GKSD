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
			return self._search(**kwargs)
		elif operation == "search_v2":									# 即将淘汰
			return self._search(**kwargs)
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
				[self.qdrant_operator.create_point_struct(word_structure['id'], word_structure['vector'])]
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

	def _search(self, id_num: Optional[str] = None, text: Optional[str] = None, vector: Optional[list] = None, logic_ask: Optional[dict] = None, **kwargs) -> List:
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
			
			# 有效的选择性补充查询
			if kwargs.get("with_xml", True):
				xml = result[1]
			else: xml = None
			if kwargs.get("vector", False):

				if kwargs.get("with_vector", False):
					xml = result[1]
					vector = xml_operator.xml_vector_partial_retrieval(xml, "BGE_large_zh_configT01")
				else: vector = None
			else:
				vector = kwargs.get("vector", False)

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
		log = "_search 开始" + log_n
		input_var = f"参数" + log_n \
			+ f"id_num\t{id_num}" + log_n \
			+ f"text\t{text}" + log_n
		log = log + input_var

		# 主函数模块
		try:
			if id_num != None:
				log = log + "基于ID搜索" + log_n
				answer = get_answer_func(
					id_num,
					with_vector=True
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
					answer_list = self._search(vector=target_vector)

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
					answer_list = self._search(vector=target_vector)
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
			log = f"gksd_operator search运行成功" + log_n \
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
	