from typing import Optional

from openai.types.chat.chat_completion import Choice
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import numpy as np
import os
import json
import traceback

import config_operator
import basic_program

# 文本向量化函数全局模型实例
_vectorization_model_instance = None

def get_model():
	"""获取全局模型实例（单例模式）"""
	global _vectorization_model_instance
	if _vectorization_model_instance is None:
		config_data = config_operator.get_config_data()
		local_model_path = f"{config_data['module_path']}bge-large-zh-v1.5"
		
		if not os.path.exists(local_model_path):
			basic_program.log_message(f"{local_model_path} 读取失败！", 50)
			raise FileNotFoundError(f"{local_model_path} 读取失败！")
		
		_vectorization_model_instance = SentenceTransformer(local_model_path)
		basic_program.log_message("文本向量化全局模型实例加载完成")
	
	return _vectorization_model_instance

def text_vectorization(text, normalize_embeddings=False):
	"""
	文本向量化函数 BGE-large-zh
	
	使用预训练的BGE-large-zh模型将输入文本转换为高维向量表示，支持单个文本或文本批量处理。
	该函数直接返回JSON字符串格式的向量，便于数据库存储。
	
	参数:
		text (str or list): 输入文本，可以是单个字符串或字符串列表
		normalize_embeddings (bool): 是否对向量进行归一化，默认为False
			- True: 输出向量将进行L2归一化，模长为1
			- False: 输出原始向量
	
	返回:
		str or list: 文本向量表示的numpy
			- 单个文本输入: 返回numpy
			- 多个文本输入: 返回numpy列表
	
	异常:
		会捕获处理过程中的异常并通过日志记录
	
	示例:
		>>> # 单个文本向量化
		>>> vector_json = text_vectorization("今天天气很好")
		>>> print(type(vector_json))  # <class 'str'>
		>>> print(vector_json[:50])   # "[-0.023, 0.156, 0.789, ...]"
		
		>>> # 批量文本向量化  
		>>> texts = ["文本1", "文本2", "文本3"]
		>>> vectors_json = text_vectorization(texts)
		>>> print(type(vectors_json))  # <class 'list'>
		>>> print(type(vectors_json[0]))  # <class 'str'>
	
	依赖:
		- 需要本地模型文件: ./module/bge-large-zh-v1.5
		- 依赖FlagEmbedding库的SentenceTransformer
		- 需要basic_program模块用于日志记录
	
	注意:
		- 模型路径为硬编码，需确保目录存在且包含完整模型文件
	"""
	try:
		model = get_model()
		# 生成文本向量
		embeddings = model.encode(
			text,
			normalize_embeddings=normalize_embeddings,
			show_progress_bar=False
		)
		

		return embeddings

	except Exception as e:
		error_traceback = traceback.format_exc()
		basic_program.log_message(f"\n    {error_traceback}", 40)
		raise e

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
		basic_program.log_message(f"Initial_Thaw_DS 出现错误\n    {e}", 50)
		raise e

def logic_PartOf(word: str, explain: str, choice_list: list):
	"""
	基于LLM的关系判断：PartOf关系

	根据给定的词语和释义，从候选列表中找出最可能作为其“整体”的词语，并判断是否符合PartOf关系定义。

	PartOf关系定义为：对象必须是整体在物理结构或功能组织上不可或缺（或极为常见）的构成单元。
	函数通过两步LLM调用完成：1)从候选列表中选择最匹配的“整体”；2)验证两者是否符合PartOf关系。

	参数:
	    word (str): 需要判断的词语（作为部分）
	    explain (str): 该词语的释义或上下文说明
	    choice_list (list): 候选“整体”词语列表

	返回:
	    str 或 None: 如果找到符合PartOf关系的“整体”词语则返回该词语，否则返回None

	报错:
	    Exception: LLM API调用失败或处理过程中出现异常时抛出

	注意:
	    1. 如果输入词语本身在候选列表中，会被自动移除
	    2. 使用DeepSeek Reasoner模型进行推理
	    3. 函数包含两次独立的LLM API调用
	    4. 所有操作会记录到系统日志中
	    5. 返回格式要求严格，仅接受'y'或'n'开头的响应
	"""
	# 输入验证
	if word in choice_list:
		new_args = []
		for choice in choice_list:
			if choice != word:
				new_args.append(choice)
		choice_list = new_args

	config_data = config_operator.get_config_data()
	llm_config = config_data["llm_api"]
	client = OpenAI(
		api_key=llm_config["api_key"],
		base_url=llm_config["base_url"],
	)
	try:
		setting_text = f"""请根据以下定义，从给定的词语列表中找出最贴近的一个词并仅返回结果。
			定义“partof”关系表示：对象必须是整体在物理结构或功能组织上不可或缺（或者极为常见）的构成单元。
			"""
		ask_text = f"""以下为需要判断的对象和释义，请找到表中的给定对象的整体
		{word} {explain}
		列表：
		{choice_list}
		"""
		response = client.chat.completions.create(
			model="deepseek-reasoner",
			messages=[
					{"role": "system", "content": f"{setting_text}"},
					{"role": "user", "content": f"{ask_text}"},
					],
			stream=False,
		)

		master_word = response.choices[0].message.content
		setting_text = f"""请根据以下定义，判断给出词语的关系，前者是否是后者的部分，是否符合partof，并返回[y/n 原因]
			定义“partof”关系表示：对象必须是整体在物理结构或功能组织上不可或缺（或者极为常见）的构成单元。

			物理结构上的部分：例如“屏幕是笔记本电脑的一部分”，屏幕是笔记本电脑物理组成的必要部件。
			功能组织上的部分：例如“引擎是汽车的一部分”，引擎是汽车发挥功能的核心组件。

			请注意：
			- 整体与部分的关系必须是直接的、典型的。例如“树叶是树的一部分”是合理的，但“树叶是森林的一部分”虽然也可以，但不如前者直接。
			- 如果两者是同一事物、并列关系、整体与部分关系颠倒、或者没有直接构成关系，则不符合partof。

			你需要按以下步骤判断：
			1. 确定两个词语在常识或专业领域中的含义。
			2. 分析前者是否在物理结构或功能组织上是后者的构成单元，且这种关系是常见或必要的。
			3. 给出判断结果和简短原因。

			输出格式必须严格为：首先输出“y”或“n”，然后空一格，接着写原因。例如：
			y 屏幕是笔记本电脑的物理构成部件。
			n 汽车不是引擎的一部分，关系颠倒。
			"""
		ask_text = f"""当前判断的两个词语：
		{word} {master_word}
		"""
		response = client.chat.completions.create(
			model="deepseek-reasoner",
			messages=[
					{"role": "system", "content": f"{setting_text}"},
					{"role": "user", "content": f"{ask_text}"},
					],
			stream=False,
		)
		if not response.choices[0].message.content:
			basic_program.log_message(f"{word}PartOf判断: {master_word} 无审核", printing = False)
			return None
		if 'y' == response.choices[0].message.content[0]:
			basic_program.log_message(f"{word} PartOf判断: {master_word} {response.choices[0].message.content}", printing = False)
			return master_word

		basic_program.log_message(f"{word}PartOf判断: {master_word} {response.choices[0].message.content}", printing = False)
		return None
	except Exception as e:
		basic_program.log_message(f"Initial_Thaw_DS 出现错误\n    {e}", 30)
		raise e

def logic_Antonym(word):
	"""
	AI词语反义词判断工具 模型代号 Initial_Thaw_DS

	该函数使用DeepSeek AI API将简短的实体名称转化为其可能的反义词，
	适用于向量数据库的实体表示生成。

	函数参数:
		word (str): 需要分析的实体名称

	函数功能:
		- 判断实体的反义词
		- 生成简洁的反义关系

	API配置:
		- 提供商: DeepSeek AI
		- 模型: deepseek-chat
		- 基础URL: https://api.deepseek.com/v1

	使用示例:
		>>> logic_Antonym("红色")
		"蓝色"
		>>> logic_Antonym("东方")  
		"西方"
		>>> logic_Antonym("红酒")
		">无结果<"

	注意:
		- 需要有效的AI API密钥
		- 函数会返回AI生成的反义词结果
	"""
	text = word
	config_data = config_operator.get_config_data()
	llm_config = config_data["llm_api"]
	client = OpenAI(
		api_key=llm_config["api_key"],
		base_url=llm_config["base_url"],
	)
	try:
		setting_text = """
		请严格依据"反义关系"识别给定对象的直接反义词。
		必须同时满足**语义对立性**和**概念对称性**标准。如果不存在符合此严格定义的反义词，则返回">无结果<"。
		
		反义关系要求两个概念在语义上形成对立，且在同一概念维度上具有对称性：
		 - **极性对立**：在连续尺度上的两端（如：热-冷、大-小）
		 - **互补对立**：非此即彼的二元关系（如：生-死、真-假）
		 - **方向对立**：在空间或时间上的相反方向（如：东-西、前-后）
		 - **关系对立**：在角色或关系上的对立（如：买-卖、父-子）
		
		必须排除的关系：
		 - **非对称关系**：两个概念不在同一语义维度或不对称（如：红酒-白酒 | 只是不同类型，不是严格反义）
		 - **程度差异**：只是程度不同而非真正对立（如：喜欢-讨厌 | 可能存在中间状态）
		 - **偶然对立**：没有必然的语义对立关系（如：苹果-橙子 | 只是不同水果）
		 - **文化偶然**：仅在特定文化背景下的对立
		
		判断标准：
		 1. 两个概念必须在同一语义场中
		 2. 必须形成明确的语义对立
		 3. 在逻辑上具有对称性
		 4. 是语言中公认的反义关系
		
		示例：
		输入：红色
		返回：蓝色
		
		输入：东方
		返回：西方
		
		输入：买
		返回：卖
		
		输入：生
		返回：死
		
		输入：红酒
		返回：>无结果<
		
		输入：苹果
		返回：>无结果<
		
		输入：喜欢
		返回：>无结果<
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
		basic_program.log_message(f"{word} 判断: {response.choices[0].message.content}", printing = False)
		return response.choices[0].message.content
	except Exception as e:
		basic_program.log_message(f"Initial_Thaw_DS 出现错误\n    {e}", 50)
		raise e

def logic_IsA(word):
	"""
	AI词语is-a关系判断工具 模型代号 Initial_Thaw_DS

	该函数使用DeepSeek AI API判断给定词语的is-a逻辑关系（上位词/下位词关系），
	适用于向量数据库的实体表示生成。

	函数参数:
		word (str): 需要分析的实体名称

	函数功能:
		- 判断实体的直接上位词（父类）
		- 生成简洁的is-a关系表示

	API配置:
		- 提供商: DeepSeek AI
		- 模型: deepseek-chat
		- 基础URL: https://api.deepseek.com/v1

	使用示例:
		>>> logic_IsA("苹果")
		"水果"
		>>> logic_IsA("汽车")  
		"交通工具"
		>>> logic_IsA("哲学")
		"学科"
		>>> logic_IsA("东西")
		">无结果<"

	注意:
		- 需要有效的AI API密钥
		- 函数会返回AI生成的is-a关系结果
	"""
	text = word
	config_data = config_operator.get_config_data()
	llm_config = config_data["llm_api"]
	client = OpenAI(
		api_key=llm_config["api_key"],
		base_url=llm_config["base_url"],
	)
	try:
		setting_text = """
		请严格依据"is-a关系"识别给定对象的直接上位词（父类概念）。
		必须同时满足**语义包含性**和**概念层次性**标准。如果不存在符合此严格定义的上位词，则返回">无结果<"。
		
		is-a关系要求两个概念在语义上形成包含关系，且具有明确的层次结构：
		 - **类属关系**：个体属于某个类别（如：苹果-水果、汽车-交通工具）
		 - **种属关系**：子类属于父类（如：哺乳动物-动物、轿车-汽车）
		 - **实例关系**：具体实例属于抽象概念（如：莎士比亚-作家、长城-建筑）
		 - **领域归属**：具体领域属于更大范畴（如：物理学-科学、唐诗-文学）
		
		必须排除的关系：
		 - **部分关系**：整体与部分的关系（如：车轮-汽车 | 这是部分关系，不是is-a）
		 - **属性关系**：对象与属性的关系（如：红色-颜色 | 这是属性关系）
		 - **功能关系**：对象与功能的关系（如：刀-切割 | 这是功能关系）
		 - **偶然关联**：没有必然的语义包含关系（如：苹果-公司 | 只是品牌关联）
		 - **过于宽泛**：上位词过于宽泛失去意义（如：苹果-物质 | 过于宽泛）
		
		判断标准：
		 1. 两个概念必须在同一语义层次结构中
		 2. 必须形成明确的语义包含关系（下位词 is a 上位词）
		 3. 在逻辑上具有层次性
		 4. 是语言中公认的类属关系
		 5. 上位词应该是直接且最接近的父类概念
		
		示例：
		输入：苹果
		返回：水果
		
		输入：汽车
		返回：交通工具
		
		输入：哲学
		返回：学科
		
		输入：唐诗
		返回：诗歌
		
		输入：东西
		返回：>无结果<
		
		输入：红色
		返回：>无结果<
		
		输入：喜欢
		返回：>无结果<
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
		basic_program.log_message(f"{word} is-a关系判断: {response.choices[0].message.content}", printing = False)
		return response.choices[0].message.content
	except Exception as e:
		basic_program.log_message(f"Initial_Thaw_DS is-a关系判断出现错误\n    {e}", 50)
		raise e

# 测试
if __name__ == "__main__":
	# print(logic_PartOf("垂体", "垂体是一种位于人和脊椎动物脑底部正中央的内分泌腺，呈椭圆形并借漏斗悬于下丘脑腹侧面。它主要通过分泌多种激素来调节生长、代谢和生殖等生理过程，与下丘脑和甲状腺等内分泌器官的功能调控密切相关。", choice_list=["大脑", "腺垂体", "神经垂体", "内分泌腺", "下丘脑", "内分泌系统", "肾上腺", "内分泌", "促黄体素", "肾"]))
	print(logic_PartOf("腺垂体", "腺垂体是垂体中由胚胎口凹的外胚层上皮发育而成的内分泌器官部分，其核心功能是合成和释放多种重要激素。它主要调节机体的生长发育、代谢平衡和生殖功能，与下丘脑和靶腺器官形成密切的神经内分泌调控轴。", choice_list=["腺垂体", "垂体", "神经垂体", "内分泌腺", "内分泌系统", "生殖激素", "卵巢功能", "下丘脑", "卵巢", "促黄体素"]))
