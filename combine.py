import os
import re
from glob import glob

def extract_number(filename):
    """从文件名中提取数字"""
    match = re.search(r'pages-(\d+)', filename)
    if match:
        return int(match.group(1))
    return float('inf')  # 如果没有找到数字，则返回一个确保最后排序的值

def merge_markdown_files(directory,book_name):
    pattern = directory + '/pages-*.md'
    file_paths = glob(pattern)
    
    # 使用自定义的extract_number函数进行排序
    file_paths.sort(key=extract_number)
    
    all_content = ''
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            all_content += content + '\n\n'
    output_path=f'/Users/a1/Downloads/sample_python_12a6ec6e-0fc3-4311-bb7f-b6c061ddad50/tencent_cloud_sample/code/final/'
    new_file_name = output_path + f'{book_name}.md'
    with open(new_file_name, 'w', encoding='utf-8') as new_file:
        new_file.write(all_content)
    
    print(f"合并完成，内容已写入{new_file_name}")
root_path='/Users/a1/Downloads/sample_python_12a6ec6e-0fc3-4311-bb7f-b6c061ddad50/tencent_cloud_sample/code/page_output/'
book_name_list=os.listdir(root_path)
xiaoxue_list=os.listdir("/Users/a1/Downloads/sample_python_12a6ec6e-0fc3-4311-bb7f-b6c061ddad50/tencent_cloud_sample/小学")
for book_name in book_name_list:
    if book_name+'.pdf' not in xiaoxue_list:
        # book_name='线性代数学习指南 居余马 第2版 清华大学出版社'
        directory_path = root_path+f'{book_name}/'  # 请替换为你的目录路径
        merge_markdown_files(directory_path,book_name)
    
    
    
    
    