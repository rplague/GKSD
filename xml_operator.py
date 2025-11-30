import xml.etree.ElementTree as ET
from xml.dom import minidom
import numpy as np
import json

def generate_empty_word_definition_xml():
	"""
	生成空内容的格式化XML字符串

	返回:
		str: 格式化的XML字符串
	"""
	xml_string = '''<?xml version="1.0" encoding="UTF-8"?>
<word_definition>
    <traditional_meaning/>
    <model_meaning/>
    <unsure_relational_meaning/>
    <relational_meaning/>
    <Template_Data_Architecture/>
</word_definition>'''
	return xml_string

def xml_update(input_xml):
	"""
	更新XML词义定义结构并转换为新格式

	该函数将原有的XML词义定义结构转换为新的格式：
	1. 将traditional_meaning中的source和data元素转换为属性+文本格式
	2. 将model_meaning中的model和data元素转换为属性+文本格式  
	3. 添加新的结构元素(unsure_relational_meaning, relational_meaning, Template_Data_Architecture)
	4. 设置版本号为1.0.0
	5. 返回格式化的XML字符串

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头

	返回:
		str: 转换后的格式化XML字符串，使用UTF-8编码和制表符缩进
	"""

	# 解析输入XML
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()

	traditional_meaning = root.find('./traditional_meaning')
	for word_meaning in traditional_meaning.findall('./word_meaning'):
		source_elem = word_meaning.find('./source')
		if source_elem is not None:
			word_meaning.set('source', source_elem.text)
			word_meaning.remove(source_elem)
			data_elem = word_meaning.find('./data')
			data_elem_text = data_elem.text
			word_meaning.remove(data_elem)
			word_meaning.text = data_elem_text
		else:
			traditional_meaning.remove(word_meaning)

	model_meaning = root.find('./model_meaning')
	for coordinate in model_meaning.findall('./coordinate'):
		model_elem = coordinate.find('./model')
		data_elem = coordinate.find('./data')
		if (model_elem is not None and model_elem.text and model_elem.text.strip() and
			data_elem is not None and data_elem.text and data_elem.text.strip()):
			coordinate.set('model', model_elem.text)
			coordinate.remove(model_elem)
			data_elem_text = data_elem.text
			coordinate.remove(data_elem)
			coordinate.text = data_elem_text
		else:
			model_meaning.remove(coordinate)

	unsure_relational_meaning = ET.SubElement(root, 'unsure_relational_meaning')
	relational_meaning = ET.SubElement(root, 'relational_meaning')
	template_data = ET.SubElement(root, 'Template_Data_Architecture') 
	root.set('version', "1.0.0")
	# 转换为格式化的XML
	def remove_whitespace(element):
		for elem in element.iter():
			if elem.text and elem.text.isspace():
				elem.text = None
			if elem.tail and elem.tail.isspace():
				elem.tail = None
	remove_whitespace(root)
	rough_string = ET.tostring(root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="    ", encoding="utf-8").decode('utf-8')

def xml_semantic_partial_adding(input_xml, source, data_input):
	"""
	向XML词义定义中添加新的词义条目

	该函数在现有的XML词义定义结构中添加一个新的词义解释条目，
	包含固定的来源信息和自定义的词义数据。

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source (str): 要添加的新词义解释来源
		data_input (str): 要添加的新词义解释内容

	返回:
		str: 添加新条目后的格式化XML字符串，使用UTF-8编码
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
	word_meaning = ET.SubElement(traditional_meaning, 'word_meaning')
	# 添加source并设置内容
	word_meaning.set('source', source)
	
	# 设置内容
	word_meaning.text = data_input
	# 转换为格式化的XML
	def remove_whitespace(element):
		for elem in element.iter():
			if elem.text and elem.text.isspace():
				elem.text = None
			if elem.tail and elem.tail.isspace():
				elem.tail = None
	remove_whitespace(root)
	rough_string = ET.tostring(root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="    ", encoding="utf-8").decode('utf-8')

def xml_vector_partial_adding(input_xml, source, data_input):
	"""
	向XML模型定义部分添加新的坐标数据

	该函数在现有的XML词义定义结构的model_meaning部分添加一个新的坐标数据条目，
	包含自定义的模型信息和坐标数据。

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source (str): 要添加的模型信息内容
		data_input (str/list): 要添加的坐标数据内容
		
	返回:
		str: 添加新坐标数据后的格式化XML字符串，使用UTF-8编码
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
	coordinate = ET.SubElement(model_meaning, 'coordinate')
	# 添加model子元素并设置内容
	coordinate.set('model', source)

	# 设置内容
	coordinate.text = str(data_input)
	# 转换为格式化的XML
	def remove_whitespace(element):
		for elem in element.iter():
			if elem.text and elem.text.isspace():
				elem.text = None
			if elem.tail and elem.tail.isspace():
				elem.tail = None
	remove_whitespace(root)
	rough_string = ET.tostring(root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="    ", encoding="utf-8").decode('utf-8')

def xml_semantic_partial_retrieval(input_xml, source):
	"""
	xml复合数据词义部分检索
	
	该函数在XML文档中查找特定来源（source）的词义定义，
	并返回对应的词义解释数据。
	
	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source: 字符串
		
	返回:
		str or None: 如果找到匹配来源的词义数据，返回对应的data文本内容；
					 如果未找到匹配项或XML结构不符合预期，返回None
	"""
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()

	word_meanings = root.findall('./traditional_meaning/word_meaning')
	if word_meanings:
		for wm in word_meanings:
			source_text = wm.get('source')
			if source_text == source:
				return wm.text
	return None

def xml_vector_partial_retrieval(input_xml, source):
	"""
	xml复合数据向量部分检索

	该函数在XML文档中查找特定来源（source）的向量数据，
	并返回对应的向量数据。

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source: 字符串

	返回:
		str or None: 如果找到匹配来源的词义数据，返回对应的list内容；
					 如果未找到匹配项或XML结构不符合预期，返回None
	"""
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()

	word_meanings = root.findall('./model_meaning/coordinate')
	if word_meanings:
		for wm in word_meanings:
			source_text = wm.get('model')
			if source_text == source:
				arr = json.loads(wm.text)
				return arr
	return None

def xml_unsure_relational_partial_adding(input_xml, source, type, id_num, confidence=0):
	"""
	向XML词义定义中添加新的不确定关系词义条目

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source (str): 要添加的新词义解释来源
		type (str): 关系类型，支持 "IsA" 或 "PartOf"
		id_num (str/int): 目标ID编号
		confidence (float): 置信度，默认为0

	返回:
		str: 添加新条目后的格式化XML字符串，使用UTF-8编码
	"""
	# 参数检查
	if type not in ["IsA", "PartOf"]:
		raise ValueError("type不支持")
	id_num = str(id_num)
	confidence = str(confidence)
	# 解析输入XML
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()
	# 找到unsure_relational_meaning元素
	unsure_relational_meaning = root.find('./unsure_relational_meaning')
	# 创建新的relation
	relation = ET.SubElement(unsure_relational_meaning, 'relation')
	# 添加参数并设置内容
	relation.set('type', type)
	relation.set('confidence', confidence)
	relation.set('source', source)
	# 创建新的target
	target = ET.SubElement(relation, 'target')
	target.text = id_num
	# 转换为格式化的XML
	def remove_whitespace(element):
		for elem in element.iter():
			if elem.text and elem.text.isspace():
				elem.text = None
			if elem.tail and elem.tail.isspace():
				elem.tail = None
	remove_whitespace(root)
	rough_string = ET.tostring(root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="    ", encoding="utf-8").decode('utf-8')

def xml_unsure_relational_partial_retrieval(input_xml):
	"""
    从XML文档中检索所有不确定关系数据
    
    该函数在XML文档中查找所有不确定关系数据，
    并返回完整的关系数据列表。

    参数:
        input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头

    返回:
        list or None: 如果找到关系数据，返回包含所有关系字典的列表；
                      如果未找到关系数据或XML结构不符合预期，返回None
    """
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()

	relations = root.findall('./unsure_relational_meaning/relation')
	answer_list = []
	if relations:
		for relation in relations:
			type = relation.get('type')
			confidence = relation.get('confidence')
			source = relation.get('source')
			text = relation.text
			_relation = {
				'type':  relation.get('type'),
				'confidence': float(relation.get('confidence')),
				'source': relation.get('source'),
				'target': int(relation.find('target').text)
			}
			answer_list.append(_relation)
		return answer_list
	return None

def xml_relational_partial_adding(input_xml, source, type, id_num, evidence_text):
	"""
	向XML词义定义中添加新的确定关系词义条目

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source (str): 新关系条目的来源
		type (str): 关系类型，支持 "IsA" 或 "PartOf"
		id_num (str/int): 目标ID编号
		evidence_text (str): 证据文本内容

	返回:
		str: 添加新条目后的格式化XML字符串，使用UTF-8编码
	"""
	# 参数检查
	if type not in ["IsA", "PartOf"]:
		raise ValueError("type不支持")
	id_num = str(id_num)
	# 解析输入XML
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()
	# 找到relational_meaning元素
	relational_meaning = root.find('./relational_meaning')
	# 创建新的relation
	relation = ET.SubElement(relational_meaning, 'relation')
	# 添加参数并设置内容
	relation.set('type', type)
	# 创建新的target
	target = ET.SubElement(relation, 'target')
	target.text = id_num
	evidence = ET.SubElement(relation, 'evidence')
	evidence.set('source', source)
	evidence.text = evidence_text
	# 转换为格式化的XML
	def remove_whitespace(element):
		for elem in element.iter():
			if elem.text and elem.text.isspace():
				elem.text = None
			if elem.tail and elem.tail.isspace():
				elem.tail = None
	remove_whitespace(root)
	rough_string = ET.tostring(root, encoding='utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="    ", encoding="utf-8").decode('utf-8')


# 测试
if __name__ == "__main__":
	input_xml = '''<?xml version="1.0" encoding="utf-8"?>
<word_definition version="1.0.0">
    <traditional_meaning>
        <word_meaning source="www.zgbk.com">唇形科鼠尾草属多年生草本或亚灌木植物。常作一年生栽培。</word_meaning>
        <word_meaning source="Initial_Thaw_DS">一串红是一种唇形科鼠尾草属的多年生观赏植物，常被作为一年生花卉栽培。其最显著特征是鲜艳的红色穗状花序和唇形花冠，具有较长的观赏期。它主要用于园林绿化、花坛布置和节日装饰，与万寿菊、矮 牵牛等常见园艺植物共同构成城市景观色彩，是典型的观赏性草本植物。</word_meaning>
    </traditional_meaning>
    <model_meaning>
        <coordinate model="BGE_large_zh_configT01">[0.01646905019879341, 0.012344327755272388]</coordinate>
    </model_meaning>
    <unsure_relational_meaning/>
    <relational_meaning/>
    <Template_Data_Architecture/>
</word_definition>'''

	print(input_xml)
	xml2 = xml_vector_partial_adding(input_xml,"www123", [1231, 1325124])
	print(xml2)
	xml3 = xml_unsure_relational_partial_adding(xml2, "source", "IsA", "7")
	print(xml3)
	answer = xml_unsure_relational_partial_retrieval(xml3)
	print(answer)
	xml4 = xml_relational_partial_adding(xml3, "本草纲目", "IsA", 123, "因为所以科学道理")
	print(xml4)
