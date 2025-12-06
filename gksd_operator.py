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
			return self._upsert(**kwargs)
		elif operation == "search":
			return self._search(**kwargs)
		else:
			raise ValueError(f"operation参数错误 无 {operation} 操作")

	def _upsert(self, auto: bool = True, **kwargs) -> bool:
		# log = f"GKSD_operator 受理添加词条\n    添加内容 {name}\t添加模式 {auto}\n    "
		def _insert_to_db(word: str, meaning_list: list, vector: dict, target_collection: str = "chn_wordlist") -> None:
			"""
			将词语及其相关信息插入数据库

			参数:
				word: 要插入的词语
				meaning_list: 含义列表，每个元素为包含source和data的字典
				vector: 向量数据，包含source和data的字典
				target_collection: Qdrant目标集合名称，默认为"chn_wordlist"

			返回:
				None

			功能说明:
				1. 生成XML数据结构并添加传统注释
				2. 添加向量标注到XML
				3. 将数据插入MariaDB数据库
				4. 获取插入记录的ID并插入Qdrant向量数据库
			"""
			xml_data = xml_operator.generate_empty_word_definition_xml()
			# 添加所有传统注释
			for meaning in meaning_list:
				source = meaning["source"]
				data = meaning["data"]
				xml_data = xml_operator.xml_semantic_partial_adding(
					xml_data,
					source,
					data
				)
			# 添加向量标注
			source = vector["source"]
			data = vector["data"]
			xml_data = xml_operator.xml_semantic_partial_adding(
				xml_data,
				source,
				str(data)
			)
			# mariadb插入
			self.mariadb_operator.safe_db_operation(
				"INSERT INTO chn_wordlist (词语, XML含义) VALUES (?, ?)",
				params=(word, xml_data,)
			)
			# qdrant插入
			id_list = self.mariadb_operator.safe_db_operation(
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
				[self.qdrant_operator.create_point_struct(id_num, vector)]
			)
		log = ""
		try:
			if auto == True:
				# 参数检查
				word = kwargs.get("word")
				if not word:
					raise ValueError("自动添加模式参数缺失")
				search_list = self._search(name=word, log_printing=False, **kwargs)
				word_list = [item["word"] for item in search_list]
				if word in word_list:
					raise ValueError("词条已存在 添加失败")
				log = log + f"确认唯一性......完成\n    "
				# 搜索来自中国网络百科全书的释义
				word_meaning = self.zgbk_searcher.search(word)
				# 获取结构化释义
				word_meaning_ITDS = ai_modules.unified_explain(word, word_meaning)
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
					params=(word, xml_data,)
				)
				# log = log + f"mariadb操作.....完成\n    "
				# qdrant插入
				id_list = self.mariadb_operator.safe_db_operation(
					"SELECT id FROM chn_wordlist WHERE 词语 = ?",
					params=(word,),
					fetch=True
				)
				if not id_list:
					raise Exception(f"回溯插入id失败 词语为{word}")
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
					vector = (vector_np + logic_add_vector_np).tolist()
					log = log + f"检测到并完成逻辑添加 {logic_add}\n    "

				log = log + f"查询vector {vector[:3]}\n    "
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
			elif id_num != None:
				log = log + f"查询条目ID {id_num}\n    "
				answer = get_answer_func(
					id_num,
					**kwargs
				)
				qdrant_answer = self.qdrant_operator.safe_qdrant_operation(
					"retrieve_points",
					target_collection,
					[id_num],
					**kwargs
				)[0]
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
