import mariadb

import config_operator


class Db_operator(object):
	def __init__(self):
		config_data = config_operator.get_config_data()
		self.config = config_data["database_data"]

	def safe_db_operation(self, operation, params=None, fetch=False):
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
			return None
		except mariadb.IntegrityError as e:
			print(f"数据完整性错误: {e}")
			if conn:
				conn.rollback()
			return None
		except mariadb.OperationalError as e:
			print(f"操作错误: {e}")
			if conn:
				conn.rollback()
			return None
		except mariadb.Error as e:
			print(f"数据库错误: {e}")
			if conn:
				conn.rollback()
			return None
		finally:
			# 使用更安全的关闭方式
			if cursor:
				cursor.close()
			if conn:
				conn.close()
	


