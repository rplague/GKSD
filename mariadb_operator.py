import mariadb
from mariadb import ConnectionPool
from typing import List, Tuple, Any, Optional, Union

import basic_program
import config_operator

class Db_operator(object):
	def __init__(self):
		config_data = config_operator.get_config_data()
		self.config = config_data["database_data"]

	def safe_db_operation(self,
						  operation: str,
						  params: Optional[Union[tuple, dict]] = None,
						  fetch: bool = False) -> Optional[Any]:
		"""
		安全的数据库操作

		Args:
			operation: SQL语句
			params: SQL参数（防止SQL注入）
			fetch: 是否获取查询结果
		"""
		conn = None
		cursor = None
		
		try:
			conn = mariadb.connect(**self.config)
			cursor = conn.cursor()
			
			# 执行数据库操作
			if params:
				cursor.execute(operation, params)
			else:
				cursor.execute(operation)
			
			# 如果是查询操作，返回结果
			if fetch:
				result = cursor.fetchall()
				return result
			else:
				# 非查询操作需要提交事务
				conn.commit()
				return cursor.rowcount  # 返回影响的行数
				
		except mariadb.ProgrammingError as e:
			print(f"SQL语法错误: {e}")
			if conn:
				conn.rollback()
			raise e
		except mariadb.IntegrityError as e:
			print(f"数据完整性错误: {e}")
			if conn:
				conn.rollback()
			raise e
		except mariadb.OperationalError as e:
			print(f"操作错误: {e}")
			if conn:
				conn.rollback()
			raise e
		except mariadb.Error as e:
			print(f"数据库错误: {e}")
			if conn:
				conn.rollback()
			raise e
		finally:
			# 使用更安全的关闭方式
			if cursor:
				cursor.close()
			if conn:
				conn.close()

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
				raise
	
	def safe_db_operation(self,
		operation: str,
		params: Optional[Union[tuple, dict]] = None,
		fetch: bool = False) -> Optional[Any]:
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
		basic_program.log_message(f"函数 safe_db_operation 开始运行\n    目标指令为 {operation}\n    参数元组为 {params}",
			printing = False)

		conn   = None
		cursor = None

		try:
			# 从连接池获取连接
			conn = self._pool.get_connection()
			cursor = conn.cursor()

			# 执行数据库操作
			if params:
				cursor.execute(operation, params)
			else:
				cursor.execute(operation)
			basic_program.log_message(f"函数 safe_db_operation 运行完成\n    执行指令为 {operation}\n    参数元组为 {params}",
				printing = False)
			# 如果是查询操作，返回结果
			if fetch:
				result = cursor.fetchall()
				return result
			else:
				# 非查询操作需要提交事务
				conn.commit()
				return cursor.rowcount

		except mariadb.ProgrammingError as e:
			if conn:
				conn.rollback()
			basic_program.log_message(f"函数 safe_db_operation 运行错误\n    执行指令为 {operation}\n    参数元组为 {params}\n    {e}",
				40,
				False)
			raise ProgrammingError(f"编程错误\n{e}")
		except mariadb.IntegrityError as e:
			if conn:
				conn.rollback()
			basic_program.log_message(f"函数 safe_db_operation 运行错误\n    执行指令为 {operation}\n    参数元组为 {params}\n    {e}",
				40,
				False)
			raise IntegrityError(f"完整性错误\n{e}")
		except mariadb.OperationalError as e:
			if conn:
				conn.rollback()
			basic_program.log_message(f"函数 safe_db_operation 运行错误\n    执行指令为 {operation}\n    参数元组为 {params}\n    {e}",
				40,
				False)
			raise OperationalError(f"操作错误\n{e}")
		except mariadb.Error as e:
			if conn:
				conn.rollback()
			basic_program.log_message(f"函数 safe_db_operation 运行错误\n    执行指令为 {operation}\n    参数元组为 {params}\n    {e}",
				40,
				False)
			raise Error(f"基础错误类\n{e}")
		finally:
			# 关闭游标，连接返回到连接池
			if cursor:
				cursor.close()
			if conn:
			    try:
			        if conn.open:
			            conn.close() 
			    except:
			        pass

	def execute_many(self, operation: str, params_list: List[Union[tuple, dict]]) -> Optional[int]:
		"""
		批量执行操作
		
		Args:
			operation: SQL语句
			params_list: 参数列表
			
		Returns:
			影响的总行数
		"""
		conn = None
		cursor = None
		
		try:
			conn = self._pool.get_connection()
			cursor = conn.cursor()
			
			cursor.executemany(operation, params_list)
			conn.commit()
			return cursor.rowcount
			
		except mariadb.Error as e:
			# logger.error(f"批量操作错误: {e}")
			if conn:
				conn.rollback()
			return None
		finally:
			if cursor:
				cursor.close()
			if conn:
				conn.close()
	
	def close_pool(self):
		"""关闭连接池"""
		if DbOperator_pool._pool:
			DbOperator_pool._pool.close()
			logger.info("数据库连接池已关闭")
	
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

