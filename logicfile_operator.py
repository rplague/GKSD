import json

class VectorIndex:
	"""建立文件位置索引，支持快速随机访问"""
	
	def __init__(self, file_path):
		self.file_path = file_path
		self.line_positions = []
		self._build_index()
	
	def _build_index(self):
		"""建立行号到文件位置的索引"""
		self.line_positions = [0]  # 第1行从位置0开始
		with open(self.file_path, 'r') as f:
			while True:
				line = f.readline()
				if not line:
					break
				self.line_positions.append(f.tell())
		self.line_positions = self.line_positions[:-1]

	def get_vector_value(self, line_num, dim):
		"""使用索引快速获取指定行"""
		if line_num < 0 or line_num >= len(self.line_positions):
			return None
			
		with open(self.file_path, 'r') as f:
			f.seek(self.line_positions[line_num])
			line = f.readline()
			# print(line[:200])
			data = json.loads(line)
			return data['vector'][dim]

	def get_vector_info(self):
		"""获取数据形状信息"""
		with open(self.file_path, 'r') as f:
			f.seek(self.line_positions[0])
			line = f.readline()
			data = json.loads(line)
		return (len(self.line_positions), len(data['vector']))