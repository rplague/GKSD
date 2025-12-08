import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from typing import List, Optional
import json

from logicfile_operator import LogicfileSetIndex

def visualize_tsne_with_labels(
	embeddings_list: List[List[float]], 
	labels: Optional[List[str]] = None,
	show_labels: bool = True,  # 新增：控制是否显示标签
	fontsize: int = 5,  # 新增：标签字体大小
	title: str = "t-SNE Visualization",
	perplexity: int = 30,
	random_state: int = 42,
	figsize: tuple = (12, 8)
) -> np.ndarray:
	"""
	使用t-SNE将1024维向量降维到2维并进行可视化，可选择在每个点旁显示标签
	"""
	
	# 1. 转换为numpy数组
	embeddings_array = np.array(embeddings_list)
	print(f"输入数据形状: {embeddings_array.shape}")
	
	# 2. 检查维度
	if embeddings_array.shape[1] != 1024:
		raise ValueError(f"期望1024维向量，但输入维度为{embeddings_array.shape[1]}")
	
	# 3. 应用t-SNE降维
	print("正在进行t-SNE降维...")
	tsne = TSNE(
		n_components=2,
		perplexity=perplexity,
		random_state=random_state,
		verbose=1
	)
	
	embeddings_2d = tsne.fit_transform(embeddings_array)
	print(f"降维后形状: {embeddings_2d.shape}")
	
	# 4. 可视化
	plt.figure(figsize=figsize)
	
	# 绘制所有点（单一颜色）
	plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], alpha=0.7, s=50, color='blue')
	
	# 5. 在每个点旁显示标签
	if show_labels and labels is not None:
		if len(labels) != len(embeddings_2d):
			raise ValueError(f"标签数量({len(labels)})与数据点数量({len(embeddings_2d)})不匹配")
		
		# 添加偏移量，避免标签重叠在点上
		offset = 1 #(embeddings_2d.max() - embeddings_2d.min()) * 0.02
		
		for i, (x, y) in enumerate(embeddings_2d):
			plt.text(x + offset, y + offset, 
					labels[i], 
					fontsize=fontsize,
					alpha=0.8,
					ha='center', va='center')
	
	# 6. 设置图表属性
	plt.title(title, fontsize=16)
	plt.xlabel("t-SNE Component 1", fontsize=12)
	plt.ylabel("t-SNE Component 2", fontsize=12)
	plt.grid(True, alpha=0.3)
	
	plt.tight_layout()
	plt.show()
	
	return embeddings_2d

# 示例使用
def main():
	index = LogicfileSetIndex("./data/PartOf.json")
	vector_info = index.get_vector_info()
	vector_list = []
	label_list = []
	print(vector_info)
	for num in range(vector_info[0]):
		vector_list.append(index.get_vector(num))
		label_list.append(index.get_value(num)['word_id'])
	# 3. 调用函数
	embeddings_2d = visualize_tsne_with_labels(
		embeddings_list=vector_list,
		labels=label_list,
		title="t-SNE Visualization of 1024-Dimensional Vectors",
		perplexity=25,
		figsize=(10, 7)
	)


if __name__ == "__main__":
	# 运行示例
	embeddings_2d = main()
