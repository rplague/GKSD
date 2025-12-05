from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PointIdsList, Filter, FilterSelector
from typing import List, Tuple, Any, Optional, Union, Dict

import basic_program
import config_operator

class Db_operator(object):
	def __init__(self):
		config_data = config_operator.get_config_data()
		self.config = config_data["database_data_v"]
		url = "http://" + self.config["host"] + ":" + self.config["port"]
		self.client = QdrantClient(url)

	def safe_qdrant_operation(self, 
							  operation: str,
							  collection_name: Optional[str] = None, 
							  data: Optional[Any] = None,
							  filters: Optional[Filter] = None,
							  **kwargs) -> Optional[Any]:
		"""
		安全的Qdrant向量数据库操作
		
		参数:
			operation: 操作类型
			collection_name: 集合名称
			data: 操作数据（向量、点等）
			filters: 过滤条件
			**kwargs: 其他参数
			
		Returns:
			操作结果
		"""
		try:
			# 集合管理操作
			if operation == "create_collection" and collection_name:
				return self._create_collection(collection_name, **kwargs)
			elif operation == "delete_collection"and collection_name:
				return self._delete_collection(collection_name)
			elif operation == "collection_info"and collection_name:
				return self._get_collection_info(collection_name)
				
			# 数据操作
			elif operation == "upsert_points"and collection_name and data:
				return self._upsert_points(collection_name, data)
			elif operation == "search_points"and collection_name and data:
				return self._search_points(collection_name, data, filters, **kwargs)
			elif operation == "retrieve_points"and collection_name and data:
				return self._retrieve_points(collection_name, data, **kwargs)
			elif operation == "delete_points"and collection_name and data:
				return self._delete_points(collection_name, data, filters)
				
			# 集合操作
			elif operation == "list_collections":
				return self._list_collections()
			elif operation == "update_aliases" and data:
				return self._update_aliases(data)
			else:
				raise ValueError(f"{operation} 或参数不符合 safe_qdrant_operation 格式要求")
				
		except Exception as e:
			raise e

	# 集合管理方法
	def _create_collection(self,
						   collection_name: str,
						   **kwargs) -> bool:
		""" 
		创建Qdrant向量数据库集合

		在Qdrant向量数据库中创建一个新的集合（collection），用于存储向量数据。
		集合是Qdrant中的基本数据组织单位，类似于传统数据库中的表。
		该函数允许自定义向量维度和距离度量方式。

		参数:
			collection_name (str): 要创建的集合名称，需唯一且符合命名规范
			**kwargs: 可选的关键字参数，包括：
				- vector_size (int): 向量的维度大小，默认为768维
				- distance (Distance): 向量距离计算方式，默认为欧几里得距离(EUCLID)

		返回:
			bool: 操作成功状态，True表示集合创建成功

		报错:
			QdrantClientError: 当集合已存在或参数无效时抛出
			ValueError: 当集合名称或向量参数无效时抛出

		注意:
			- 集合名称在同一Qdrant实例中必须唯一
			- 创建集合后无法修改向量配置（维度和距离度量）
			- 建议在创建集合前检查是否已存在同名集合
			- 向量维度应与后续插入的向量数据维度一致
			- 支持的距离度量包括：EUCLID（欧几里得）、COSINE（余弦）、DOT（点积）
		"""
		vector_size = kwargs.get("vector_size", 1024)
		distance = kwargs.get("distance", Distance.EUCLID)
		self.client.create_collection(
			collection_name=collection_name,
			vectors_config=VectorParams(
				size=vector_size, 
				distance=distance)
		)
		return True

	def _update_aliases(self,
						actions: List) -> bool:
		"""
		更新别名

		函数用途：更新集合别名

		用于修改Qdrant向量数据库中集合的别名配置，可以添加、删除或修改集合的别名引用。

		参数:
			actions (List): 包含别名操作对象的列表，每个操作对象定义要执行的别名变更操作

		返回:
			bool: 操作成功返回True，失败时抛出异常

		报错:
			DbOperatorError: 当别名操作执行失败时抛出，包含具体的错误信息
			ValueError: 当提供的actions参数无效时抛出

		示例:
			none

		注意:
			- 别名操作是原子性的，要么全部成功，要么全部失败
			- 可以同时执行多个别名操作
			- 别名用于为集合提供可读的名称引用，便于管理和维护
			- 操作前建议验证集合是否存在
		"""
		self.client.update_collection_aliases(
			change_aliases_operations=actions
		)
		return True

	def _delete_collection(self,
						   collection_name: str) -> bool:
		""" 
		删除指定的向量数据库集合
		
		永久删除Qdrant数据库中的指定集合及其所有数据。
		此操作不可逆，会删除集合中的所有向量点和元数据。
		
		参数:
			collection_name (str): 要删除的集合名称，必须是已存在的集合
		
		返回:
			success (bool): 操作是否成功，True表示删除成功
		
		报错:
			ValueError: 当集合名称无效或为空时
			ConnectionError: 当数据库连接失败时
			CollectionNotFoundError: 当指定的集合不存在时
			PermissionError: 当没有删除集合的权限时
		
		示例:
			operator._delete_collection("my_collection")
		
		注意:
			- 此操作会永久删除集合中的所有数据，无法恢复
			- 在执行删除前建议先备份重要数据
			- 删除操作需要相应的数据库权限
			- 删除大型集合可能需要较长时间
		"""
		self.client.delete_collection(collection_name)
		return True

	def _get_collection_info(self,
							 collection_name: str) -> Dict:
		""" 
		获取指定集合的详细信息
		
		用于检索Qdrant向量数据库中特定集合的配置信息、状态统计和元数据。
		该函数返回集合的完整描述，包括向量参数、索引状态、分片信息等。
		
		参数:
			collection_name (str): 要查询的集合名称，必须是在数据库中已存在的集合
		
		返回:
			collection_info (Dict): 包含集合详细信息的字典，通常包括：
			  - status: 集合状态（green/yellow/red）
			  - vectors_count: 向量数量
			  - segments_count: 段数量
			  - config: 集合配置信息
			  - payload_schema: 负载数据结构
		
		报错:
			ValueError: 当集合名称不存在或格式无效时抛出
			ConnectionError: 当无法连接到数据库时抛出
			UnexpectedResponse: 当数据库返回意外响应时抛出
		
		注意:
			- 集合必须存在，否则会抛出异常
			- 返回的信息包含实时统计数据和配置信息
			- 该操作是只读的，不会修改集合状态
		"""
		return self.client.get_collection(collection_name)

	def _list_collections(self) -> List:
		"""列出所有集合"""
		return self.client.get_collections().collections

	# 数据操作方法
	def _upsert_points(self,
					   collection_name: str,
					   points: List[PointStruct]) -> bool:
		""" 
		向量数据库点数据插入或更新操作

		执行批量插入或更新向量数据库中的点数据。
		如果点ID已存在则更新该点，否则插入新点。

		参数:
		    collection_name (str): 目标集合名称，用于指定操作的数据表
		    points (List[PointStruct]): 点数据列表，每个点包含ID、向量和可选的有效载荷

		返回:
		    bool: 操作成功状态，True表示操作完成

		报错:
		    ValueError: 参数验证失败或数据格式错误

		注意:
		    - 操作是原子性的，要么全部成功要么全部失败
		    - 建议批量操作时控制单次数据量，避免内存溢出
		    - 点ID应为唯一标识，重复ID将触发更新操作
		"""
		self.client.upsert(
			collection_name=collection_name,
			points=points
		)
		return True

	def _search_points(self,
					   collection_name: str,
					   query_vector: List[float],
					   filters: Optional[Filter] = None,
					   **kwargs) -> List:
		""" 
		在指定集合中搜索与查询向量相似的向量点
		
		基于向量相似度搜索，返回与查询向量最接近的多个向量点。
		支持过滤条件、分页和结果定制。
		
		参数:
			collection_name (str): 要搜索的集合名称
			query_vector (List[float]): 查询向量，用于相似度比较
			filters (Optional[Filter]): 过滤条件，用于筛选搜索结果，默认None
			**kwargs: 其他可选参数
				- limit (int): 返回结果数量，默认10
				- score_threshold (float): 相似度分数阈值，仅返回高于此阈值的结果
				- with_payload (bool): 是否返回payload数据，默认True
				- with_vectors (bool): 是否返回向量数据，默认False
		
		返回:
			List[ScoredPoint]: 包含搜索结果的对象列表，每个对象包含：
				- id: 点的唯一标识符
				- score: 相似度分数（距离分数）
				- payload: 点的附加数据（如果with_payload为True）
				- vector: 点的向量数据（如果with_vectors为True）

		报错:
			ValueError: 当查询向量维度与集合向量维度不匹配时
		
		注意:
			- 相似度分数基于集合创建时指定的距离度量方式计算
			- 对于欧几里得距离，分数越小表示越相似
			- 过滤条件可以基于payload中的字段进行筛选
			- 查询向量必须与集合中向量的维度一致
		"""
		limit = kwargs.get("limit", 10)
		score_threshold = kwargs.get("score_threshold")
		with_payload = kwargs.get("with_payload", True)
		with_vectors = kwargs.get("with_vectors", False)
		
		return self.client.search(
			collection_name=collection_name,
			query_vector=query_vector,
			query_filter=filters,
			limit=limit,
			score_threshold=score_threshold,
			with_payload=with_payload,
			with_vectors=with_vectors
		)



	def _retrieve_points(self,
						 collection_name: str,
						 ids: List[Union[str, int]],
						 **kwargs) -> List:
		""" 
		根据ID检索向量点

		从指定的集合中根据点ID列表检索对应的向量点信息，可以控制是否返回payload和向量数据。

		参数:
			collection_name (str): 要查询的集合名称
			ids (List[Union[str, int]]): 要检索的点ID列表，支持字符串或整数类型的ID
			**kwargs: 可选参数
				with_payload (bool): 是否返回payload数据，默认为True
				with_vectors (bool): 是否返回向量数据，默认为False

		返回:
			List[Record]: 检索到的点记录列表，每个记录包含ID、可选的payload和向量数据

		报错:
			QdrantClientError: Qdrant客户端操作错误
			ValueError: 参数验证失败
			CollectionNotFoundError: 指定的集合不存在

		注意:
			- 如果指定的ID在集合中不存在，该ID会被静默忽略
			- 返回列表中的记录顺序可能与请求的ID顺序不一致
			- 当with_vectors=True时，响应数据量会显著增加
			- 建议仅在需要时启用with_vectors选项以优化性能
		"""
		with_payload = kwargs.get("with_payload", True)
		with_vectors = kwargs.get("with_vectors", False)
		
		return self.client.retrieve(
			collection_name=collection_name,
			ids=ids,
			with_payload=with_payload,
			with_vectors=with_vectors
		)

	def _delete_points(self,
					   collection_name: str, 
					   points: Optional[List[Union[str, int]]] = None,
					   filters: Optional[Filter] = None) -> bool:
		""" 
		删除向量数据库中的点数据

		从指定的集合中删除一个或多个点数据。
		支持通过点ID列表或过滤器条件两种方式删除数据。
		该操作用于清理无效数据、更新数据集或维护数据库内容。

		参数:
			collection_name (str): 要操作的集合名称，指定数据所在的集合
			points (Optional[List[Union[str, int]]]): 要删除的点ID列表，通过具体的点标识符指定删除目标
			filters (Optional[Filter]): 过滤条件对象，通过条件表达式筛选要删除的数据点

		返回:
			bool: 操作执行状态，成功返回True，失败会抛出异常

		报错:
			ValueError: 当未提供points或filters参数时抛出，表示删除条件不足

		注意:
			- 删除操作不可逆，请谨慎使用
			- 如果同时提供points和filters，points参数会被优先使用
			- 批量删除大量数据时建议使用过滤器方式，性能更优
		"""
		if points:
			self.client.delete(
				collection_name=collection_name,
				points_selector=PointIdsList(
					points=points
				)
			)
		elif filters:
			self.client.delete(
				collection_name=collection_name,
				points_selector=FilterSelector(
					filter=filters
				)
			)
		else:
			raise ValueError("必须提供points或filters参数")
		return True


	# 便捷方法
	def create_point_struct(self,
							id,
							vector,
							payload = None) -> PointStruct:
		"""创建点结构"""
		return PointStruct(
			id=id,
			vector=vector,
			payload=payload
		)