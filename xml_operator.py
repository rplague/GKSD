import xml.etree.ElementTree as ET
from xml.dom import minidom

def test_operation_001(input_xml):
	"""
	将输入的XML结构转换为标准化的词义定义格式
	
	该函数将输入的XML文档结构重新组织，主要处理以下转换：
	1. 将嵌套的word_meaning元素提取到traditional_meaning下
	2. 为model_meaning部分创建标准化的坐标数据结构
	3. 保持原有的source和data内容不变

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头

	返回:
		str: 转换后的格式化XML字符串，使用UTF-8编码

	返回:
		>>> input_xml = '<?xml version="1.0"?><word_definition>...</word_definition>'
		>>> result = test_operation_001(input_xml)
		>>> print(result)
	"""
	# 解析输入XML
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()

	# 创建新的根元素
	new_root = ET.Element('word_definition')
	
	# 处理 traditional_meaning 部分
	traditional_meaning = ET.SubElement(new_root, 'traditional_meaning')
	
	# 查找所有word_meaning元素
	word_meanings = root.findall('.//word_meaning')
	
	if word_meanings:
		for wm in word_meanings:
			new_word_meaning = ET.SubElement(traditional_meaning, 'word_meaning')

			# 复制所有子元素
			for child in wm:
				new_elem = ET.SubElement(new_word_meaning, child.tag)
				new_elem.text = child.text

	# 处理 model_meaning 部分
	model_meaning = ET.SubElement(new_root, 'model_meaning')
	coordinate = ET.SubElement(model_meaning, 'coordinate')

	# 创建model元素并添加注释
	model_elem = ET.SubElement(coordinate, 'model')
	model_elem.append(ET.Comment(' 模型信息 '))

	# 创建data元素并添加注释  
	data_elem = ET.SubElement(coordinate, 'data')
	data_elem.append(ET.Comment(' 坐标数据 '))
	
	# 转换为格式化的XML
	rough_string = ET.tostring(new_root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)
	
	return reparsed.toprettyxml(indent=" ", encoding="utf-8").decode('utf-8')

def test_operation_002_0(input_xml):
	"""
	根据指定来源查询词义数据
	
	该函数在XML文档中查找特定来源（www.zgbk.com）的词义定义，
	并返回对应的词义解释数据。
	
	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		
	返回:
		str or None: 如果找到匹配来源的词义数据，返回对应的data文本内容；
					 如果未找到匹配项或XML结构不符合预期，返回None
		
	返回:
		>>> xml_data = '<?xml version="1.0"?><word_definition>...</word_definition>'
		>>> result = test_operation_002_0(xml_data)
		>>> print(result)  # 输出：一种通用的过程式编程语言。
	"""
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()

	word_meanings = root.findall('./traditional_meaning/word_meaning')
	if word_meanings:
		for wm in word_meanings:
			source_elem = wm.find('source')
			source_text = source_elem.text
			if source_text == "www.zgbk.com":
				data_elem = wm.find('data')
				data_text = data_elem.text
				return data_text
	return None

def test_operation_002_1(input_xml, source_input, data_input):
	"""
	向XML词义定义中添加新的词义条目
	
	该函数在现有的XML词义定义结构中添加一个新的词义解释条目，
	包含固定的来源信息和自定义的词义数据。
	
	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source_input (str): 要添加的新词义解释来源
		data_input (str): 要添加的新词义解释内容

		
	返回:
		str: 添加新条目后的格式化XML字符串，使用UTF-8编码
		
	示例:
		>>> xml_data = '<?xml version="1.0"?><word_definition>...</word_definition>'
		>>> 新词义 = "这是新的词义解释"
		>>> 结果 = test_operation_002_1(xml_data, 新词义)
		>>> print(结果)
	"""
	# 解析输入XML
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()
	# 找到traditional_meaning元素
	traditional_meaning = root.find('./traditional_meaning')
	# 创建新的word_meaning
	new_wm = ET.SubElement(traditional_meaning, 'word_meaning')
	# 添加source子元素并设置内容
	source_elem = ET.SubElement(new_wm, 'source')
	source_elem.text = source_input
	
	# 添加data子元素并设置内容
	data_elem = ET.SubElement(new_wm, 'data')
	data_elem.text = data_input
	# 转换为格式化的XML
	rough_string = ET.tostring(new_root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)

	return reparsed.toprettyxml(indent=" ", encoding="utf-8").decode('utf-8')

def test_operation_002_2(input_xml, model_input, data_input):
	"""
	向XML模型定义部分添加新的坐标数据

	该函数在现有的XML词义定义结构的model_meaning部分添加一个新的坐标数据条目，
	包含自定义的模型信息和坐标数据。

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		model_input (str): 要添加的模型信息内容
		data_input (str): 要添加的坐标数据内容
		
	返回:
		str: 添加新坐标数据后的格式化XML字符串，使用UTF-8编码

	示例:
		>>> xml数据 = '<?xml version="1.0"?><word_definition>...</word_definition>'
		>>> 模型信息 = "BERT模型"
		>>> 坐标数据 = "向量坐标信息"
		>>> 结果 = test_operation_002_2(xml数据, 模型信息, 坐标数据)
		>>> print(结果)
	"""
	# 解析输入XML
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()
	# 找到traditional_meaning元素
	model_meaning = root.find('./model_meaning')
	# 创建新的word_meaning
	new_cd = ET.SubElement(model_meaning, 'coordinate')
	# 添加model子元素并设置内容
	model_elem = ET.SubElement(new_cd, 'model')
	model_elem.text = model_input

	# 添加data子元素并设置内容
	data_elem = ET.SubElement(new_cd, 'data')
	data_elem.text = data_input
	# 转换为格式化的XML
	rough_string = ET.tostring(new_root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)

	return reparsed.toprettyxml(indent=" ", encoding="utf-8").decode('utf-8')
# 测试
if __name__ == "__main__":
	input_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<word_definition>
	<traditional_meaning>
		<Noun>
			<word_meaning>
				<source>www.zgbk.com</source>
				<data>一种通用的过程式编程语言。</data>
			</word_meaning>
		</Noun>
	</traditional_meaning>
	<model_meaning/>
</word_definition>'''

	result = test_operation_001(input_xml)
	print("转换结果:")
	print(result)