import mariadb
from mariadb import ConnectionPool
import traceback
from typing import List, Tuple, Any, Optional, Union

import basic_program
import config_operator

class Db_operator(object):
	def __init__(self):
		config_data = config_operator.get_config_data()
		self.config = config_data["database_data"]

	def safe_db_operation(self, operation: str, params: Optional[Union[tuple, dict]] = None, fetch: bool = False, **kwargs) -> Optional[Any]:
		"""
		安全的数据库操作

		参数:
			operation (str): SQL语句
			params (list/tuple): SQL参数（防止SQL注入）
			fetch (bool): 是否获取查询结果

		"""
		level = 20
		log_n = "\n    "
		log = "safe_db_operation 开始" + log_n
		input_var = f"参数" + log_n \
			+ f"operation\t{operation}" + log_n \
			+ f"params\t{params}" + log_n \
			+ f"fetch\t{fetch}" + log_n
		log = log + input_var

		conn = None
		cursor = None

		try:
			conn = mariadb.connect(**self.config)
			cursor = conn.cursor()
			log = log + "数据连接\t完成" + log_n
			# 执行数据库操作
			if params:
				cursor.execute(operation, params)
			else:
				cursor.execute(operation)
			log = log + "指令执行\t完成" + log_n

			# 如果是查询操作，返回结果
			if fetch:
				result = cursor.fetchall()

			else:
				# 非查询操作需要提交事务
				conn.commit() # 返回影响的行数
				result = cursor.rowcount
			log = f"safe_db_operation 运行成功" + log_n \
				+ input_var
			return result	
		except mariadb.Error as e:
			level = 50
			if conn:
				conn.rollback()
			error_traceback = traceback.format_exc()
			log = log + f"错误类型\t{type(e).__name__}" + log_n\
				+ f"错误信息\t{str(e)}" + log_n\
				+ f"完整栈追踪:\n{error_traceback}"
			raise e
		finally:
			# 使用更安全的关闭方式
			if cursor:
				cursor.close()
			if conn:
				conn.close()
			if kwargs.get("log_printing", False) and level == 20:
				basic_program.log_message(log, level, kwargs.get("log_printing", False))

class DbOperator_pool(object):
	"""
	数据库操作类 - 使用连接池管理数据库连接
	"""
	
	# 类变量，共享连接池
	_pool = None
	
	def __init__(self, pool_size: int = 5):
		"""
		初始化数据库操作器
		
		Args:
			pool_size: 连接池大小，默认5个连接
		"""
		config_data = config_operator.get_config_data()
		self.db_config = config_data["database_data"]
		self.pool_size = pool_size
		
		# 初始化连接池
		self._init_pool()
	
	def _init_pool(self):
		"""初始化数据库连接池"""
		if DbOperator_pool._pool is None:
			try:
				DbOperator_pool._pool = ConnectionPool(
					pool_name="main_pool",
					pool_size=self.pool_size,
					**self.db_config
				)
			except mariadb.Error as e:
				raise e
	
	def safe_db_operation(self, operation: str, params: Optional[Union[tuple, dict]] = None, fetch: bool = False, **kwargs) -> Optional[Any]:
		"""
		安全的数据库操作
		
		通用性较强的数据库指令操作模块

		参数:
			operation (str): SQL语句
			params (Optional[Union[tuple, dict]]): SQL参数（防止SQL注入）
			fetch (bool): 是否获取查询结果

		返回:
			查询操作返回结果列表，非查询操作返回影响行数

		报错:
			ValueError: operation 指令未能获取
			ProgrammingError: 编程错误
			IntegrityError: 完整性错误
			OperationalError: 操作错误
			Error: 基础错误类（非以上错误）
			
		注意:
			- 数据库操作出现报错后程序会自动回滚
		"""
		# 输入验证
		if not operation:
			raise ValueError("operation 不能为空")

		# 记录函数调用
		level = 20
		log_n = "\n    "

		conn   = None
		cursor = None
		log = f"safe_db_operation 运行成功" + log_n \
				+ f"参数" + log_n \
				+ f"operation\t{operation}" + log_n \
				+ f"params\t{params}" + log_n \
				+ f"fetch\t{fetch}" + log_n
		try:
			# 从连接池获取连接
			conn = self._pool.get_connection()
			cursor = conn.cursor()

			# 执行数据库操作
			if params:
				cursor.execute(operation, params)
			else:
				cursor.execute(operation)

			# 如果是查询操作，返回结果
			if fetch:
				result = cursor.fetchall()

			else:
				# 非查询操作需要提交事务
				conn.commit() # 返回影响的行数
				result = cursor.rowcount
			return result

		except mariadb.Error as e:
			level = 50
			if conn:
				conn.rollback()
			error_traceback = traceback.format_exc()
			log = "safe_db_operation" + f"错误类型\t{type(e).__name__}" + log_n\
				+ f"错误信息\t{str(e)}" + log_n\
				+ f"完整栈追踪:\n{error_traceback}"
			raise e

		finally:
			# 关闭游标，连接返回到连接池
			if cursor:
				cursor.close()
			if kwargs.get("log_printing", False) and level == 20:
				basic_program.log_message(log, level, kwargs.get("log_printing", False))
	
	def close_pool(self):
		"""关闭连接池"""
		if DbOperator_pool._pool:
			DbOperator_pool._pool.close()
	
	def get_pool_stats(self) -> dict:
		"""
		获取连接池统计信息
		
		Returns:
			连接池统计信息字典
		"""
		if not self._pool:
			return {}
		
		return {
			"active_connections": self._pool.active_connections,
			"total_connections": self._pool.total_connections,
			"max_size": self.pool_size
		}


# 使用示例
if __name__ == "__main__":
	# 创建数据库操作器实例
	db = DbOperator_pool(pool_size=5)
	
	try:
		# 查看连接池状态
		stats = db.get_pool_stats()
		print(f"连接池状态: {stats}")
		
	finally:
		# 应用结束时关闭连接池
		db.close_pool()
