from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os

import config_operator
import basic_program

def text_vectorization(text, normalize_embeddings = True):
	"""
	文本向量化函数 BGE-large-zh
	
	使用预训练的BGE-large-zh模型将输入文本转换为高维向量表示，支持单个文本或文本批量处理。
	该函数适用于文本相似度计算、语义搜索、聚类分析等自然语言处理任务。
	
	参数:
		text (str or list): 输入文本，可以是单个字符串或字符串列表
		normalize_embeddings (bool): 是否对向量进行归一化，默认为True
			- True: 输出向量将进行L2归一化，模长为1
			- False: 输出原始向量
	
	返回:
		numpy.ndarray: 文本向量表示
			- 单个文本输入: 返回1维数组，形状为(embedding_dim,)
			- 多个文本输入: 返回2维数组，形状为(batch_size, embedding_dim)
			- 处理失败时: 返回None
	
	异常:
		会捕获处理过程中的异常并通过日志记录，返回None
	
	示例:
		>>> # 单个文本向量化
		>>> vector = text_vectorization("今天天气很好")
		>>> print(vector.shape)  # (1024,)
		
		>>> # 批量文本向量化
		>>> texts = ["文本1", "文本2", "文本3"]
		>>> vectors = text_vectorization(texts)
		>>> print(vectors.shape)  # (3, 1024)
		
		>>> # 禁用归一化
		>>> vector = text_vectorization("测试文本", normalize_embeddings=False)
	
	依赖:
		- 需要本地模型文件: ./module/bge-large-zh-v1.5
		- 依赖FlagEmbedding库的SentenceTransformer
		- 需要basic_program模块用于日志记录
	
	注意:
		- 模型路径为硬编码，需确保目录存在且包含完整模型文件
	"""

	# 设置本地模型路径debug
	config_data = config_operator.get_config_data()
	local_model_path = f"{config_data["module_path"]}bge-large-zh-v1.5"  # 替换为你的实际路径
	# 检查模型是否存在，如果不存在则报错
	if not os.path.exists(local_model_path):
		basic_program.log_message(f"{local_model_path} 读取失败！", 50)
		return None
	try:
		# 生成文本向量
		embeddings = model.encode(
			text,
			normalize_embeddings=normalize_embeddings,
			show_progress_bar=False
		)
		return embeddings
	except Exception as e:
		basic_program.log_message(f"{e}", 40)
		return None

def unified_explain(word, explain):
	"""
	AI词语含义格式化工具 模型代号 Initial_Thaw_DS

	该函数使用DeepSeek AI API将简短的实体名称和解释转化为结构化的详细描述，
	适用于向量数据库的实体表示生成。

	函数参数:
		word (str): 需要解释的实体名称（如"苹果"、"牛顿"等）
		explain (str): 实体的简要解释或定义

	函数功能:
		- 根据实体类型自动选择合适的模板（基础定义、人物传记、事件历史、抽象概念）
		- 生成丰富、精准、结构化的文本描述
		- 优化语义信息，消除歧义，明确逻辑关系
		- 输出格式化的实体描述文本

	API配置:
		- 提供商: DeepSeek AI
		- 模型: deepseek-chat
		- 基础URL: https://api.deepseek.com/v1

	使用示例:
		>>> unified_explain("苹果", "蔷薇科苹果属植物")
		>>> unified_explain("牛顿", "英国著名的物理学家和数学家")

	注意:
		- 需要有效的DeepSeek API密钥
		- 函数会返回AI生成的格式化结果
	"""
	text = word + " " + explain
	config_data = config_operator.get_config_data()
	llm_config = config_data["llm_api"]
	client = OpenAI(
		api_key=llm_config["api_key"],
		base_url=llm_config["base_url"],
	)
	try:
		setting_text = """
		# 系统角色设定
		你是一个专门为向量数据库生成高质量实体解释的AI助手。
		你的任务是将用户提供的简短实体名称，转化为一段丰富、精准、结构化的文本描述。
		这段描述将用于生成该实体的向量表示，因此必须最大化语义信息，消除歧义，并明确逻辑关系。
		根据百科词条的类型，选择合适的模板来构建这句话：
		- 基础定义版
		{实体}是一种{类别}，{核心特征/定义}。它主要用于{功能/用途}，与{相关概念A}和{相关概念B}密切相关。
		示例：
			输入：苹果 蔷薇科苹果属植物。
			输出：苹果是一种蔷薇科水果，外形圆形或椭圆，味道甜美多汁。它主要作为食物直接食用或用于制作果汁和甜点，与维生素C和健康饮食密切相关。
			输入：数据库 按照一定的结构化方式组织和存储的数据集合。
			输出：数据库是一种按照数据结构来组织、存储和管理数据的计算机软件。它主要用于高效地存储、查询和操作大量数据，与SQL查询语言和服务器后端开发密切相关。
		- 人物传记版
		{人物}是一位{国籍}{时代}{职业}，以{主要成就}而闻名。他/她提出了{理论/发现}，对{影响领域}产生了深远影响。
		示例：
			输入：牛顿 英国著名的物理学家和数学家，英国皇家学会会长。
			输出：艾萨克·牛顿是一位英国17世纪的物理学家和数学家，以提出牛顿运动定律和万有引力定律而闻名。他提出了经典力学的基本框架，并对物理学、天文学和现代科学产生了深远影响。
		- 事件历史版
		{事件}是发生于{时间}在{地点}的一个历史事件，其主要内容是{事件概述}。该事件导致了{结果/影响}，标志着{历史意义}。
		示例：
			输入：波士顿倾茶事件 北美殖民地时期波士顿人民反对英国东印度公司对北美殖民地的茶叶贸易垄断权的事件。又称波士顿茶党案。
			输出：波士顿倾茶事件是发生于1773年在北美殖民地波士顿的一个政治抗议事件，其主要内容是殖民地居民为反对英国茶叶税而将东印度公司的茶叶倒入海中。该事件加剧了英国与殖民地的矛盾，标志着美国独立战争的前奏。
		- 抽象概念版
		{概念}是一种关于{领域}的{理论/思想/方法}，其核心观点是{核心内容}。该概念由{提出者}提出，用于解决{问题}，并与{相关概念}形成对比或补充。
		示例：
			输入：供给侧改革 从提高供给质量出发，用改革的办法推进结构调整，矫正要素配置扭曲，扩大有效供给，提高供给结构对需求变化的适应性和灵活性，提高全要素生产率，更好地满足广大人民群众的需要，促进经济社会持续健康发展。又称供给侧结构性改革。
			输出：供给侧改革是一种关于经济发展的宏观经济政策，其核心观点是通过优化生产要素配置来提升经济增长的质量和效率。该概念由经济学家提出，用于解决产能过剩和经济结构失衡问题，并与需求侧管理形成互补。
		"""
		ask_text = f"{text}"
		response = client.chat.completions.create(
			model="deepseek-chat",
			messages=[
					{"role": "system", "content": f"{setting_text}"},
					{"role": "user", "content": f"{ask_text}"},
					],
			stream=False,
		)
		basic_program.log_message(f"{word} 格式化：\n    {response.choices[0].message.content}", printing = False)
		basic_program.log_message(f"{word} 解释格式化已完成")
		return response.choices[0].message.content
	except Exception as e:
		basic_program.log_message(f"{e}", 40)

# 测试
if __name__ == "__main__":
	unified_explain("牛顿", "国际单位制中表示力的单位")