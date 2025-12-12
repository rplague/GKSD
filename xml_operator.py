from typing import Optional, Union, Any
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

def xml_check(input_xml: str, auto: bool = False, id_num: Optional[int] = None):
	"""
	检查xml格式并返回

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		
	返回:

		str: 成功返回str
	"""
	if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
		root = ET.fromstring(input_xml)
	else:
		tree = ET.parse(input_xml)
		root = tree.getroot()
	answer = True

	# # 普通释义重复检查
	# # 每个来源只允许拥有一个普通释义
	# source_list = root.findall('./traditional_meaning/word_meaning/source')
	# if len(source_list) != len(set(source_list)):
	# 	word_meaning_list = root.findall('./traditional_meaning/word_meaning')
	# 	if len(word_meaning_list) != len(set(word_meaning_list)):
	# 		return False # auto可解决
	# 	else:
	# 		return False

	# # 几何释义重复检查
	# # 每个来源只允许拥有一个几何释义
	# model_list = root.findall('./model_meaning/coordinate/model')
	# if len(model_list) != len(set(model_list)):
	# 	coordinate_list = root.findall('./model_meaning/coordinate')
	# 	if len(coordinate_list) != len(set(coordinate_list)):
	# 		return False # auto可解决
	# 	else:
	# 		return False

	# 不确定逻辑关系重复检查
	# 不确定逻辑不允许重复
	# 不确定逻辑不允许引用自身
	# 自动修复以前者为准
	relations = root.findall('./unsure_relational_meaning/relation')
	relation_list = []
	for relation in relations:
		relation_list.append({
			'type': relation.get('type'),
			'target': int(relation.find('target').text)
		})

	# if len(relation_list) != len(set(relation_list)):
	# 	return False
	if id_num:
		unsure_relational_meaning = root.find('./unsure_relational_meaning')
		relations = root.findall('./unsure_relational_meaning/relation')
		for relation in relations:
			target = relation.find('./target')
			xml_id = target.text
			if id_num == int(xml_id):
				answer = False
				if auto == True:
					unsure_relational_meaning.remove(relation)
				else:
					return False
	if answer == False and auto == True:
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
	
	return True

def xml_check_v2(input_xml: str, auto: bool = False, id_num: Optional[int] = None) -> Any:
	"""
	检查xml格式并返回

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		auto (bool): 是否自动修复问题
		id_num (int): 检查是否引用自身ID

	返回:
		str/bool: 成功返回格式化XML字符串，失败返回False或错误信息
	"""
	try:
		if isinstance(input_xml, str) and input_xml.strip().startswith('<?xml'):
			root = ET.fromstring(input_xml)
		else:
			tree = ET.parse(input_xml)
			root = tree.getroot()
	except ET.ParseError as e:
		return f"XML解析错误: {e}"
	except Exception as e:
		return f"文件读取错误: {e}"
	
	# 检查根元素
	if root.tag != 'word_definition':
		return "根元素必须是'word_definition'"
	
	# 检查版本属性
	version = root.get('version')
	if not version:
		return "缺少version属性"
	
	# 收集所有问题
	problems = []
	fixes_applied = []
	
	# 1. 普通释义重复检查
	word_meanings = root.findall('./traditional_meaning/word_meaning')
	source_dict = {}
	duplicate_word_meanings = []
	
	for wm in word_meanings:
		source = wm.get('source', '')
		if source in source_dict:
			duplicate_word_meanings.append((source_dict[source], wm))
		else:
			source_dict[source] = wm
	
	if duplicate_word_meanings:
		problems.append(f"发现重复的普通释义来源: {[s for s,_ in duplicate_word_meanings]}")
		if auto:
			# 保留第一个，删除后续重复的
			for _, duplicate_wm in duplicate_word_meanings:
				parent = duplicate_wm.getparent()
				if parent is not None:
					parent.remove(duplicate_wm)
			fixes_applied.append("已删除重复的普通释义")
	
	# 2. 几何释义重复检查
	coordinates = root.findall('./model_meaning/coordinate')
	model_dict = {}
	duplicate_coordinates = []
	
	for coord in coordinates:
		model = coord.get('model', '')
		if model in model_dict:
			duplicate_coordinates.append((model_dict[model], coord))
		else:
			model_dict[model] = coord
	
	if duplicate_coordinates:
		problems.append(f"发现重复的几何释义模型: {[m for m,_ in duplicate_coordinates]}")
		if auto:
			# 保留第一个，删除后续重复的
			for _, duplicate_coord in duplicate_coordinates:
				parent = duplicate_coord.getparent()
				if parent is not None:
					parent.remove(duplicate_coord)
			fixes_applied.append("已删除重复的几何释义")
	
	# 3. 不确定逻辑关系检查
	unsure_relations = root.findall('./unsure_relational_meaning/relation')
	relation_set = set()
	duplicate_relations = []
	self_references = []
	
	for relation in unsure_relations:
		# 检查必需属性
		rel_type = relation.get('type')
		confidence = relation.get('confidence')
		source = relation.get('source', '')
		
		if not rel_type:
			problems.append("不确定关系缺少type属性")
		if confidence is None:
			problems.append("不确定关系缺少confidence属性")
		elif not re.match(r'^0(\.\d+)?$', confidence):
			problems.append(f"confidence值格式错误: {confidence}")
		
		# 检查target
		target_elem = relation.find('target')
		if target_elem is None or not target_elem.text:
			problems.append("不确定关系缺少target元素")
		else:
			try:
				target_id = int(target_elem.text.strip())
				# 检查是否引用自身
				if id_num is not None and target_id == id_num:
					self_references.append(relation)
				
				# 检查重复
				rel_key = (rel_type, target_id, source)
				if rel_key in relation_set:
					duplicate_relations.append(relation)
				else:
					relation_set.add(rel_key)
			except ValueError:
				problems.append(f"target ID不是有效整数: {target_elem.text}")
	
	if duplicate_relations:
		problems.append(f"发现{len(duplicate_relations)}个重复的不确定关系")
		if auto:
			for rel in duplicate_relations:
				parent = rel.getparent()
				if parent is not None:
					parent.remove(rel)
			fixes_applied.append("已删除重复的不确定关系")
	
	if self_references:
		problems.append(f"发现{len(self_references)}个引用自身ID({id_num})的不确定关系")
		if auto:
			for rel in self_references:
				parent = rel.getparent()
				if parent is not None:
					parent.remove(rel)
			fixes_applied.append("已删除引用自身的不确定关系")
	
	# 4. 确定逻辑关系检查
	relational_meaning = root.find('./relational_meaning')
	if relational_meaning is not None:
		relations = relational_meaning.findall('relation')
		for relation in relations:
			rel_type = relation.get('type')
			if not rel_type:
				problems.append("确定关系缺少type属性")
			
			# 检查target
			target_elem = relation.find('target')
			if target_elem is None or not target_elem.text:
				problems.append("确定关系缺少target元素")
			else:
				try:
					target_id = int(target_elem.text.strip())
					# 检查是否引用自身
					if id_num is not None and target_id == id_num:
						problems.append("确定关系引用了自身ID")
				except ValueError:
					problems.append(f"确定关系的target ID不是有效整数: {target_elem.text}")
			
			# 检查evidence
			evidence_elem = relation.find('evidence')
			if evidence_elem is None:
				problems.append("确定关系缺少evidence元素")
			else:
				evidence_source = evidence_elem.get('source', '')
				if not evidence_source:
					problems.append("evidence缺少source属性")
				if not evidence_elem.text or not evidence_elem.text.strip():
					problems.append("evidence缺少内容")
	
	# 5. 检查Template_Data_Architecture是否存在
	template = root.find('./Template_Data_Architecture')
	if template is None:
		problems.append("缺少Template_Data_Architecture元素")
	
	# 如果有问题且不自动修复，返回错误信息
	if problems and not auto:
		return {
			'status': False,
			'problems': problems,
			'message': f"发现{len(problems)}个问题"
		}
	
	# 如果有问题但自动修复了，或者没有问题
	if auto and (problems or fixes_applied):
		# 清理空白
		def remove_whitespace(element):
			for elem in element.iter():
				if elem.text and elem.text.isspace():
					elem.text = None
				if elem.tail and elem.tail.isspace():
					elem.tail = None
		
		remove_whitespace(root)
		
		# 生成格式化的XML
		rough_string = ET.tostring(root, encoding='utf-8')
		reparsed = minidom.parseString(rough_string)
		formatted_xml = reparsed.toprettyxml(indent="    ", encoding="utf-8").decode('utf-8')
		
		return {
			'status': True,
			'xml': formatted_xml,
			'fixes_applied': fixes_applied,
			'original_problems': problems if problems else []
		}
	
	# 没有问题的正常情况
	if not problems:
		return {
			'status': True,
			'message': "XML格式检查通过"
		}
	
	return False

# 辅助函数：验证单个关系
def validate_relation(relation_elem: ET.Element, is_unsure: bool = True):
	"""验证单个关系元素"""
	problems = []
	
	if is_unsure:
		# 检查不确定关系
		confidence = relation_elem.get('confidence')
		if confidence is None:
			problems.append("缺少confidence属性")
		elif not re.match(r'^0(\.\d+)?$', confidence):
			problems.append(f"confidence值格式错误: {confidence}")
	
	# 检查type
	rel_type = relation_elem.get('type')
	if not rel_type:
		problems.append("缺少type属性")
	
	# 检查target
	target_elem = relation_elem.find('target')
	if target_elem is None:
		problems.append("缺少target元素")
	elif not target_elem.text or not target_elem.text.strip():
		problems.append("target元素为空")
	else:
		try:
			int(target_elem.text.strip())
		except ValueError:
			problems.append(f"target ID不是有效整数: {target_elem.text}")
	
	return problems


def xml_semantic_partial_adding(
	input_xml,
	source,
	data_input):
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

def xml_vector_partial_adding(
	input_xml,
	source,
	data_input):
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

def xml_semantic_partial_retrieval(
	input_xml,
	source):
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

def xml_vector_partial_retrieval(
	input_xml,
	source):
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

def xml_unsure_relational_partial_adding(
	input_xml: str,
	source: str,
	type: str,
	id_num: Union[str, int],
	confidence: float = 0.0):
	"""
	向XML词义定义中添加新的不确定关系词义条目

	参数:
		input_xml (str): XML字符串或XML文件路径。如果是字符串，必须以'<?xml'开头
		source (str): 要添加的新待定逻辑解释来源
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
	# 重复检查
	answer_list = xml_unsure_relational_partial_retrieval(input_xml)
	for item in answer_list:
		if item['type'] == type and item['target'] == target:
			raise ValueError("数据条目重复")
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

def xml_relational_partial_adding(
	input_xml,
	source,
	type,
	id_num,
	evidence_text):
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
		<word_meaning source="www.zgbk.com">垂体中由胚胎口凹的外胚层上皮发育而成的部分。</word_meaning>
		<word_meaning source="www.zgbk.com">垂体中由胚胎口凹的外胚层上皮发育而成的部分。</word_meaning>
		<word_meaning source="Initial_Thaw_DS">腺垂体是垂体中由胚胎口凹的外胚层上皮发育而成的内分泌器官部分，其核心功能是合成和释放多种重要激素。它主要调节机体的生长发育、代谢平衡和生殖功能，与下丘脑和靶腺器官形成密切的神经内分泌调控轴。</word_meaning>
	</traditional_meaning>
	<model_meaning>
		<coordinate model="BGE_large_zh_configT01">[0.02093636430799961, 0.009262663312256336, -0.05891106277704239]</coordinate>
	</model_meaning>
	<unsure_relational_meaning>
		<relation type="PartOf" confidence="0.2" source="Initial_Thaw_DS">
			<target>5414</target>
		</relation>
		<relation type="PartOf" confidence="0.2" source="Initial_Thaw_DS">
			<target>17490</target>
		</relation>
	</unsure_relational_meaning>
	<relational_meaning/>
	<Template_Data_Architecture/>
</word_definition>'''

	# print(input_xml)
	xml2 = xml_check_v2(input_xml, auto=True, id_num=17490)
	print(xml2)
	