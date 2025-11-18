from typing import List, Tuple, Any, Optional, Union, Dict
import traceback

import basic_program
import ai_modules
import mariadb_operator
import qdrant_operator
import xml_operator
from server import web_search

class GKSD_operator(object):
	def __init__(self):
		log = "GKSD_operator 初始化\n    "
		try:
			level = 20
			self.mariadb_operator = mariadb_operator.Db_operator()
			log = log + "mariadb_operator\t初始化完成\n    "
			self.qdrant_operator = qdrant_operator.Db_operator()
			log = log + "qdrant_operator\t初始化完成\n    "
			self.zgbk_searcher = web_search.ZgbkSearcher()
			log = log + "zgbk_searcher\t初始化完成\n    "
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
		level = 20
		log = f"GKSD_operator 受理添加词条\n    添加内容 {name}\n    添加模式 {auto}\n    "
		try:
			if auto == True:
				search_list = self._search(**kwargs)
				word_list = [word for word, meaning in search_list]
				if name in word_list:
					raise ValueError("词条已存在 添加失败")
				log = log + f"确认唯一性......完成\n    "
				# 搜索来自中国网络百科全书的释义
				word_meaning = self.zgbk_searcher.search(name)
				log = log + f"搜索释义........完成\n    "
				# 获取结构化释义
				word_meaning_ITDS = ai_modules.unified_explain(word_meaning)
				log = log + f"结构化释义......完成\n    "
				# 获取向量坐标
				word_meaning_BGE_large_zh_configT01 = ai_modules.text_vectorization(word_meaning_ITDS)
				log = log + f"生成坐标........完成\n    "
				# xml字符操作
				xml_data = xml_semantic_partial_adding(xml_operator.generate_empty_word_definition_xml(),
													   "www.zgbk.com",
													   word_meaning)
				xml_data = xml_semantic_partial_adding(xml_data,
													   "Initial_Thaw_DS",
													   word_meaning_ITDS)
				xml_data = xml_vector_partial_adding(xml_data,
													 "BGE_large_zh_configT01",
													 word_meaning_BGE_large_zh_configT01)
				log = log + f"xml生成.........完成\n    "
				# mariadb插入
				self.mariadb_operator.safe_db_operation(
					"INSERT INTO chn_wordlist (词语, XML含义) VALUES (?, ?)",
					params=(name, xml_data,)
				)
				log = log + f"mariadb操作.....完成\n    "
				# qdrant插入
				id_list = self.mariadb_operator.safe_db_operation(
					"SELECT id FROM chn_wordlist WHERE 词语 = ?",
					params=(name,),
					fetch=True
				)
				id_num = id_list[0]
				target_collection = "chn_wordlist"

				self.qdrant_operator.safe_qdrant_operation(
					"upsert_points",
					target_collection,
					[self.qdrant_operator.create_point_struct(int(id_num),
														 	 word_meaning_BGE_large_zh_configT01.tolist())]
				)
				log = log + f"qdrant操作......完成\n    "

			else:
				raise Exception("半自动添加方法未构建")
		except Exception as e:
			level = 30
			log = log + f"GKSD_operator\t添加词条失败\n详细信息：\n\n{e}"
		finally:
			basic_program.log_message(log, level)
			return level == 20

	def _search(self,
				name: str,
				**kwargs) -> List:
		"""
		基于语义的汉语词典查询

		使用BGE向量模型将查询文本转换为向量表示，在Qdrant向量数据库中进行相似度搜索，
		然后从MySQL数据库获取完整的词语信息和XML含义解析，返回语义相关的词语列表。

		参数:
			name (str): 查询文本，支持任意长度的中文文本
			**kwargs: Qdrant搜索的可选参数，用于自定义搜索行为

		返回:
			list: 包含(词语, 含义)元组的列表，按相似度降序排列
				- 词语 (str): 词典中的标准词语
				- 含义 (str): 从XML中解析出的语义解释

		报错:
			FileNotFoundError: BGE模型文件不存在
			ConnectionError: 数据库连接失败
			ValueError: 输入参数格式错误
			Exception: 其他处理过程中的异常

		注意:
			- 函数内部使用向量相似度搜索，返回语义相关而非精确匹配的结果
			- 查询过程涉及多个系统组件，性能受网络和硬件资源影响
			- 返回结果数量受Qdrant配置和score_threshold参数限制
			- XML解析依赖特定的语义标签结构"Initial_Thaw_DS"
		"""
		try:
			level = 20
			log = f"GKSD_operator 受理查询\n    查询内容 {name}\n    "
			vector_partial = ai_modules.text_vectorization(name).tolist()
			log = log + "........向量化完成\n    "
			target_collection = "chn_wordlist"
			answer_list = self.qdrant_operator.safe_qdrant_operation("search_points",
																	 target_collection,
																	 vector_partial,
																	 with_payload = False,
																	 **kwargs)
			log = log + "........向量查询完成\n    "
			for index, answer in enumerate(answer_list):
				result = self.mariadb_operator.safe_db_operation(
					"SELECT 词语, XML含义 FROM chn_wordlist WHERE id = ?", 
					params=(answer.id,),
					fetch=True
				)
				word, xml_meaning = result[0]
				meaning = xml_operator.xml_semantic_partial_retrieval(xml_meaning, "Initial_Thaw_DS")
				answer_list[index] = (word, meaning)
			log = log + "........词条查询完成\n    查询结束并返回查询结果"
		except Exception as e:
			level = 40
			error_traceback = traceback.format_exc()
			err_log = f"    错误类型\t{type(e).__name__}\n    错误信息\t{str(e)}\n    完整栈追踪:\n{error_traceback}"
			log = log + "GKSD_operator\n查询任务失败\n详细信息：\n" + err_log
			raise e
		finally:
			basic_program.log_message(log, level)
			return answer_list

