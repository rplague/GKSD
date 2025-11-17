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
		if auto == True:
			level = 20
			log = f"GKSD_operator 受理自动添加词条\n    添加内容 {name}\n    "
			search_list = self._search(**kwargs)
			word_list = [word for word, meaning in search_list]
			if name in word_list:
				raise ValueError("词条已存在 添加失败")
			return False

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

