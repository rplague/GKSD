from typing import Optional
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

def logic_PartOf(word: str, explain: str, choice_list: Optional[list] = None):
	"""
	
	"""
	config_data = config_operator.get_config_data()
	llm_config = config_data["llm_api"]
	client = OpenAI(
		api_key=llm_config["api_key"],
		base_url=llm_config["base_url"],
	)
	try:
		if choice_list == None:
			setting_text = f"请严格依据“部分-整体关系”识别给定对象的直接父类（即其所属的整体）。"
			f"必须同时满足**结构性**和**依存性**标准。如果不存在符合此严格定义的父类，则返回“>无结果<”。"
			f"part-of关系要求“部分”是构成“整体”的一个**物理或功能性的组成部分**，且该部分在逻辑上**依赖于**整体的存在或定义。"
			f"- **物理构成**：部分是整体在物理结构上的一块（如：发动机是汽车的组成部分）。"
			f"- **功能性构成**：部分是整体在功能上的一个子模块（如：章节是书籍的功能性组成部分）。"
			f"- **依存性**：部分不能独立于其整体而被完整定义或理解（车轮本身是一个物体，但作为“汽车的车轮”时，其身份依赖于汽车）。"

			f"必须排除的关系："
			f" - **分类关系（is-a/hypernym）**：对象是整体的一個类别或子类（如：苹果 -> 水果）。"
			f" - **实例关系（instance-of）**：对象是整体的一个具体实例（如：泰山 -> 山脉）。"
			f" - **所有权关系（has-a）**：整体拥有该对象，但该对象不是其结构性组成部分（如：公司 -> 员工 | 员工是成员，但不是结构部件；正确的part-of是`部门 -> 公司`）。"
			f" - **随意或松散的整体**：对象与整体之间没有必然的结构性联系（如：沙子 -> 沙滩 | 沙滩是沙子的松散集合，并非一个功能整体）。"
			f"示例："
			f"输入：汽油发动机 汽油发动机是一种以内燃机为工作原理的动力装置，以汽油作为燃料并通过燃烧将化学能转化为机械动能。它主要用于驱动汽车、摩托车和小型机械设备，与燃油喷射系统和涡轮增压技术密切相关。"
			f"返回：汽车"

			f"输入：主根 主根是一种由植物胚根顶端分生组织发育形成的主要根系结构，其核心特征是垂直向下生长并形成植物的初生根轴。它主要用于固定植物体、吸收土壤深层水分和养分，并与侧根和不定根共同构成完整的植物根系系统。"
			f"返回：植物"

			f"输入：苹果 苹果是一种蔷薇科苹果属的落叶乔木果实，外形呈圆形或椭圆形，果皮多为红色、黄色或绿色，果肉清脆多汁且富含维生素和膳食纤维。它主要作为新鲜水果直接食用，也可加工成果汁、果酱、蜜饯等食品，与人体健康维护和日常饮食营养均衡密切相关。"
			f"返回：>无结果<"

			f"输入：员工 员工是一种在就业组织中从事具体工作的人员，本身不具有基本经营决策权力并从属于这种管理结构。他们主要根据组织安排执行任务并获取劳动报酬，与雇佣合同和职业发展密切相关。"
			f"返回：>无结果<"
				
			f"输入：爱情 爱情是一种关于人际关系的强烈情感体验，是人际吸引的最高表现形式，其核心特征包括亲密感、承诺和激情。它主要作为建立长期伴侣关系的基础，与亲情、友情等情感形式密切相关，并深刻影响着个体的心理健康和社会行为模式。"
			f"返回：>无结果<"
			ask_text = f"{word} {explain}"
		else:
			setting_text = f"""
请根据“结构性部分-整体关系”识别给定对象的直接父类。
对象必须是整体在**物理结构或功能组织上不可或缺的构成单元**。

**关键区分**：
- ✅ **结构性部分**：对象是整体物理结构或功能系统的一部分（如：花瓣 -> 花朵）
- ❌ **集合性部分**：对象是整体集合中的一个成员（如：玫瑰 -> 花园 | 士兵 -> 军队）
- ❌ **类别性部分**：对象是整体类别中的一个子类（如：一串红 -> 观赏植物）

**合格的关系必须满足**：
1. 对象在物理上或功能上**嵌入**在整体中
2. 移除该对象会影响整体的**结构完整性**或**功能完整性**
3. 对象与整体有明确的**结构边界**和**空间包含关系**

**必须严格排除**：
1. **任何分类/子类关系**（is-a）：对象是整体的一种类型
2. **任何成员-集合关系**：对象只是整体集合中的一个元素
3. **任何实例-类别关系**：对象是整体概念的一个具体例子

**特别针对植物的反例**：
- ❌ 一串红 -> 观赏植物（这是分类关系：一串红是一种观赏植物）
- ❌ 花瓣 -> 植物（这是错误的层级：花瓣是花朵的一部分，花朵才是植物的一部分）
- ✅ 花瓣 -> 花朵（正确：花瓣是花朵的物理部件）
- ✅ 根系 -> 植物（正确：根系是植物的功能系统）

**判断流程**：
1. 首先检查：对象是否是整体的一种类型或实例？如果是 → 排除
2. 然后检查：对象是否在物理上构成整体的一部分？如果不是 → 排除
3. 最后检查：如果整体是一个集合，对象是否只是其中的成员？如果是 → 排除

**示例**：
输入：花瓣 [花朵, 植物, 花蕊, 花萼, 观赏植物, 开花植物, 花冠, 雄蕊, 雌蕊]
返回：花朵

输入：一串红 [千日红, 观赏植物, 珍珠梅, 矮牵牛, 万寿菊, 雁来红, 一枝黄花, 蛇目菊, 三色堇]
返回：>无结果<

输入：汽油发动机 [汽油机, 汽油车, 内燃机, 燃气轮机, 汽轮机, 柴油发动机, 汽油, 柴油机, 车用汽油]
返回：汽油车

**最终规则**：
如果对象是整体的一个**子类、实例或成员**，而不是其**结构组件**，一律返回">无结果<"
"""
			ask_text = word + " ["
			for choice in choice_list:
				ask_text = ask_text + choice + ", "
			ask_text = ask_text + "]"
		response = client.chat.completions.create(
			model="deepseek-chat",
			messages=[
					{"role": "system", "content": f"{setting_text}"},
					{"role": "user", "content": f"{ask_text}"},
					],
			stream=False,
		)
		basic_program.log_message(f"{word} PartOf判断: {response.choices[0].message.content}", printing = False)
		return response.choices[0].message.content
	except Exception as e:
		basic_program.log_message(f"Initial_Thaw_DS 出现错误\n    {e}", 50)
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
	print(logic_PartOf("雨刷器"))