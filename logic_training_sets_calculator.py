import os
import json
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm


'''
脚本任务：
- 计算逻辑json的向量特点并保存数据
'''

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

def calculate_variance_std_numpy(data, ddof=0):
	"""
	使用numpy计算列表数据的方差和标准差

	参数:
	data: 数值列表或numpy数组
	ddof: 自由度调整 (0: 总体方差, 1: 样本方差)

	返回:
	(方差, 标准差, 均值)
	"""
	if not data:
		raise ValueError("列表不能为空")

	# 转换为numpy数组
	arr = np.array(data)

	# 计算方差和标准差
	mean = np.mean(arr)
	variance = np.var(arr, ddof=ddof)
	std_deviation = np.sqrt(variance)

	return variance, std_deviation, mean

def quartiles_method(sorted_data):
	"""
	计算四分位数
	
	参数:
	sorted_data -- 已经排序的数值列表
	
	返回:
	(Q1, Q2, Q3) - 第一四分位数、中位数、第三四分位数
	"""
	if not sorted_data:
		raise ValueError("列表不能为空")
	
	n = len(sorted_data)
	
	def find_quantile(p):
		"""找到指定分位数的位置"""
		pos = (n - 1) * p
		left = int(pos)
		right = left + 1
		weight = pos - left
		
		if right >= n:
			return sorted_data[left]
		return sorted_data[left] * (1 - weight) + sorted_data[right] * weight

	Q1 = find_quantile(0.25)
	Q2 = find_quantile(0.5)  # 中位数
	Q3 = find_quantile(0.75)

	return Q1, Q2, Q3

def mad_method(data, median = None):
	"""
	直接从数据计算中位数绝对偏差
	
	参数:
	data -- 数据列表
	median -- 中位数（可选）
	返回:
	MAD值
	"""
	if not data:
		raise ValueError("数据列表不能为空")
	n = len(data)
	
	# 计算中位数
	if median == None:
		sorted_data = sorted(data)
		
		if n % 2 == 1:
			median = sorted_data[n // 2]
		else:
			median = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
	
	# 计算每个数据点与中位数的绝对偏差
	absolute_deviations = [abs(x - median) for x in data]
	
	# 计算绝对偏差的中位数
	sorted_deviations = sorted(absolute_deviations)
	if n % 2 == 1:
		mad = sorted_deviations[n // 2]
	else:
		mad = (sorted_deviations[n // 2 - 1] + sorted_deviations[n // 2]) / 2
	
	return mad


index = VectorIndex("./data/Antonym.json") # 数据集输入位置
vector_info = index.get_vector_info()
stats_dict = []


for dimension in tqdm(range(vector_info[1]), desc="处理维度"):
	datas = []
	for row in range(vector_info[0]):
		datas.append(index.get_vector_value(row, dimension))
	datas = sorted(datas)
	variance, std_deviation, mean = calculate_variance_std_numpy(datas)
	Q1, Q2, Q3 = quartiles_method(datas)
	max_data, min_data = datas[-1], datas[0]
	IQR = Q3 - Q1
	MAD = mad_method(datas, Q2)
	Skewness = 3.0 * (mean - Q2) / std_deviation
	# Skewness > 0 : 右偏 ; |Skewness| < 0.5 : 大致对称

	data = {
	"dimension": dimension,
	# 集中趋势度量
	"mean": mean,
	
	# 离散程度度量
	"variance": variance,
	"standard_deviation": std_deviation,
	"interquartile_range": IQR,
	"median_absolute_deviation": MAD,
	
	# 五数概括（Five-number summary）
	"minimum": min_data,
	"first_quartile": Q1,
	"median": Q2,
	"third_quartile": Q3,
	"maximum": max_data,

	"Skewness": Skewness}
	with open("output.txt", "a", encoding="utf-8") as output_file:
		json.dump(data, output_file, ensure_ascii=False, indent=4)
	stats_dict.append({
			'med': Q2,
			'q1': Q1,
			'q3': Q3,
			'whislo': min_data,
			'whishi': max_data,
			'fliers': []
		})

# 制图
fig, ax = plt.subplots(figsize=(8, 6))
ax.bxp(stats_dict, 
	showfliers=True,      	# 显示异常值
	patch_artist=True,    	# 填充颜色
	showmeans=False,      	# 不显示均值
)
ax.set_ylabel('Values')
ax.set_title(f'Boxplot from Dimension 1 to {dimension + 1}')
plt.grid(True, alpha=0.3)
plt.show()
