import json
import re

def parse_major_tables(text):
    """
    解析专业分类表格文本，转换为JSON格式
    """
    # 按学科大类分割文本
    sections = re.split(r'##\s*(.+?)\n', text)[1:]  # 从第一个有效内容开始
    
    result = {}
    current_category = None
    
    for i in range(0, len(sections), 2):
        if i + 1 < len(sections):
            category_name = sections[i].strip()
            table_content = sections[i + 1]
            
            # 解析表格内容
            majors = parse_table(table_content)
            
            result[category_name] = {
                "category_name": category_name,
                "majors": majors
            }
    
    return result

def parse_table(table_text):
    """
    解析单个表格内容
    """
    lines = table_text.strip().split('\n')
    majors = []
    
    # 跳过表头行（以 | ---- | 开头的行）
    header_line_found = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查是否是表头分隔线
        if re.match(r'^\|?\s*-+\s*\|', line):
            header_line_found = True
            continue
            
        # 跳过表头标题行（在分隔线之前）
        if not header_line_found:
            continue
            
        # 解析数据行
        if line.startswith('|'):
            # 移除首尾的 | 并分割
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) >= 3:
                major = {
                    "discipline_class": cells[0],
                    "code": cells[1],
                    "major_name": cells[2]
                }
                majors.append(major)
    
    return majors

def save_to_json(data, filename):
    """
    将数据保存为JSON文件
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 读取输入文件
    input_file = "专业分类"
    output_file = "专业分类.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析数据
        parsed_data = parse_major_tables(content)
        
        # 保存为JSON
        save_to_json(parsed_data, output_file)
        
        print(f"转换完成！结果已保存到 {output_file}")
        print(f"共解析了 {len(parsed_data)} 个学科大类")
        
        # 打印统计信息
        total_majors = 0
        for category, data in parsed_data.items():
            count = len(data["majors"])
            total_majors += count
            print(f"  {category}: {count} 个专业")
        
        print(f"总计: {total_majors} 个专业")
        
    except FileNotFoundError:
        print(f"错误：找不到输入文件 {input_file}")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

# 如果直接运行脚本
if __name__ == "__main__":
    main()