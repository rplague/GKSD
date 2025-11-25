import json
import os
class LogicfileSetIndex:
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

	def get_value(self, line_num):
		"""使用索引快速获取指定行"""
		if line_num < 0 or line_num >= len(self.line_positions):
			return None
			
		with open(self.file_path, 'r') as f:
			f.seek(self.line_positions[line_num])
			line = f.readline()
			# print(line[:200])
			data = json.loads(line)
			return data

	def get_vector_info(self):
		"""获取数据形状信息"""
		with open(self.file_path, 'r') as f:
			f.seek(self.line_positions[0])
			line = f.readline()
			data = json.loads(line)
		return (len(self.line_positions), len(data['vector']))

	def __len__(self):
		return len(self.line_positions)

	def __getitem__(self, key):
		return self.get_value(key)


class LogicfileIndex:
	"""建立文件位置索引，支持快速随机访问多行JSON数据"""
	
	def __init__(self, file_path):
		self.file_path = file_path
		self.json_positions = []  # 存储每个JSON对象的起始位置
		self._cached_data = {}
		self._build_index()

	def _build_index(self):
		"""建立JSON对象到文件位置的索引"""
		if not os.path.exists(self.file_path):
			raise FileNotFoundError(f"文件不存在: {self.file_path}")
			
		self.json_positions = []
		with open(self.file_path, 'r', encoding='utf-8') as f:
			brace_count = 0
			in_json = False
			json_start_pos = 0
			
			while True:
				pos = f.tell()
				char = f.read(1)
				
				if not char:  # 文件结束
					break
					
				if char == '{':
					if brace_count == 0:
						# 新的JSON对象开始
						json_start_pos = pos
						in_json = True
					brace_count += 1
					
				elif char == '}':
					brace_count -= 1
					if brace_count == 0 and in_json:
						# 一个完整的JSON对象结束
						self.json_positions.append(json_start_pos)
						in_json = False

	def _read_json_object(self, start_pos):
		"""从指定位置读取完整的JSON对象"""
		with open(self.file_path, 'r', encoding='utf-8') as f:
			f.seek(start_pos)
			
			brace_count = 0
			json_content = ""
			in_json = False
			
			while True:
				char = f.read(1)
				if not char:
					break
					
				json_content += char
				
				if char == '{':
					brace_count += 1
					in_json = True
				elif char == '}':
					brace_count -= 1
					if brace_count == 0 and in_json:
						# 找到完整的JSON对象
						break
			
			return json_content

	def get_value(self, json_index):
		"""获取指定索引的JSON对象"""
		if json_index < 0 or json_index >= len(self.json_positions):
			return None
			
		# 检查缓存
		if json_index in self._cached_data:
			return self._cached_data[json_index]
			
		try:
			json_str = self._read_json_object(self.json_positions[json_index])
			data = json.loads(json_str)
			self._cached_data[json_index] = data
			return data
			
		except (json.JSONDecodeError, IOError) as e:
			print(f"读取JSON对象错误 (索引 {json_index}): {e}")
			return None

	def get_all_values(self):
		"""获取所有JSON对象"""
		return [self.get_value(i) for i in range(len(self.json_positions))]

	def __len__(self):
		return len(self.json_positions)

	def __getitem__(self, key):
		return self.get_value(key)