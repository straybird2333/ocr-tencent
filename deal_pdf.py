import multiprocessing


import hashlib
import hmac
import json
import sys
import time
from datetime import datetime
from tqdm import tqdm
if sys.version_info[0] <= 2:
    from httplib import HTTPSConnection
else:
    from http.client import HTTPSConnection

import base64
import os

def delete_folder(folder_path):
    # 检查文件夹是否存在
    if os.path.exists(folder_path):
        # 删除文件夹中的文件
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                os.remove(file_path)

        # 删除文件夹本身
        os.rmdir(folder_path)
        print(f"文件夹 '{folder_path}' 及其下所有文件已被删除。")
    else:
        print(f"文件夹 '{folder_path}' 不存在。")
        
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def file_to_base64(file_path):
    with open(file_path, "rb") as file:
        encoded_string = base64.b64encode(file.read())
        return encoded_string.decode("utf-8")

def get_page(image_base64,type):
    '''
    给出base64编码，格式，返回的markdown的结果
    '''
    
    secret_id=''
    secret_key=''

    token = ""
    service = "ocr"
    host = "ocr.tencentcloudapi.com"
    region = "ap-guangzhou"
    version = "2018-11-19"
    action = "ReconstructDocument"
    
    
    if type=='PDF':
        image_base64="data:application/pdf;base64,"+image_base64
        payload={"FileType":"PDF",
            "FileBase64":f"{image_base64}"}
        payload=json.dumps(payload,indent=None,ensure_ascii=False)

    # params = json.loads(payload)
    # params=payload
    endpoint = "https://ocr.tencentcloudapi.com"
    algorithm = "TC3-HMAC-SHA256"
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (ct, host, action.lower())
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (http_request_method + "\n" +
                        canonical_uri + "\n" +
                        canonical_querystring + "\n" +
                        canonical_headers + "\n" +
                        signed_headers + "\n" +
                        hashed_request_payload)

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (algorithm + "\n" +
                    str(timestamp) + "\n" +
                    credential_scope + "\n" +
                    hashed_canonical_request)

    # ************* 步骤 3：计算签名 *************
    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (algorithm + " " +
                    "Credential=" + secret_id + "/" + credential_scope + ", " +
                    "SignedHeaders=" + signed_headers + ", " +
                    "Signature=" + signature)

    # ************* 步骤 5：构造并发起请求 *************
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": timestamp,
        "X-TC-Version": version
    }
    if region:
        headers["X-TC-Region"] = region
    if token:
        headers["X-TC-Token"] = token
    resp=''
    try:
        req = HTTPSConnection(host)
        time.sleep(1)
        req.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
        
        resp = req.getresponse()
        t=resp.read()
        t=t.decode('utf-8')
        t=json.loads(t)
        try:
            md_base64=t['Response']['MarkdownBase64']
        except:
            print(t)
        decoded_string = base64.b64decode(md_base64).decode('utf-8')
        return decoded_string
    except Exception as err:
        print(err)
        return ''


import fitz  # PyMuPDF

def split_pdf(input_path, dir_path):
    """
    将一个PDF文件按页拆分为多个单独的PDF文件。
    
    :param input_path: 输入的PDF文件路径
    :param dir_path: 保存拆分后PDF文件的目录路径
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)  # 如果目录不存在，则创建
    
    doc = fitz.open(input_path)  # 打开PDF文件
    total_pages = len(doc)
    pages_per_file = 4  # 每个文件包含的页数
    total_error=0
    for i in range(0, total_pages, pages_per_file):
        # 创建一个新的文档
        new_doc = fitz.Document()
        
        # 添加三页到新文档中
        for j in range(pages_per_file):
            if i + j < total_pages:
                try:
                    new_doc.insert_pdf(doc, from_page=i + j, to_page=i + j)
                except:
                    total_error+=1
                    continue
        
        # 构建输出文件名并保存
        output_filename = f"pages-{i + 1}.pdf"
        output_path = os.path.join(dir_path, output_filename)
        new_doc.save(output_path)
        new_doc.close()  # 关闭新文档以释放资源
    print('split-error-page: ',total_error)
    doc.close()  # 关闭原PDF文档





def process_page(temp_pdf_path, page, output_root, book_name):
    page_path = os.path.join(temp_pdf_path, page)
    base64_data = file_to_base64(page_path)
    md_str = get_page(base64_data, type="PDF")
    ouptut_page = page.replace(".pdf", '.md')
    output_path = os.path.join(output_root, book_name)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    with open(os.path.join(output_path, ouptut_page), 'w') as fout:
        fout.write(md_str)




if __name__ == "__main__":
    root_path = '/Users/a1/Downloads/sample_python_12a6ec6e-0fc3-4311-bb7f-b6c061ddad50/tencent_cloud_sample/小学' # 处理pdf的路径
    temp_path = '/Users/a1/Downloads/sample_python_12a6ec6e-0fc3-4311-bb7f-b6c061ddad50/tencent_cloud_sample/code/temp'  # 存放临时的路径
    output_root = '/Users/a1/Downloads/sample_python_12a6ec6e-0fc3-4311-bb7f-b6c061ddad50/tencent_cloud_sample/code/page_output'  # 输出路径
    pdf_list = os.listdir(root_path)
    for pdf in tqdm(pdf_list):
        if '.pdf' not in pdf:
            continue
        book_name=pdf.replace('.pdf','')
        input_path=root_path+'/'+pdf # 原pdf路径
        temp_pdf_path=temp_path+'/'+book_name # 临时拆分的路径
        split_pdf(input_path,temp_pdf_path) # 生成临时文件
        page_list=os.listdir(temp_pdf_path)

        
        ### 这里可使用多进程改写
        for page in tqdm(page_list):
            process_page(temp_pdf_path,page,output_root=output_root,book_name=book_name)

        ###
        delete_folder(temp_pdf_path) # 删除临时文件
    
        
    
    
    # # 使用多进程处理每个PDF页******没弄好
    # processes = []
    # max_processes=4
    # for i, pdf in enumerate(pdf_list):
    #     p = multiprocessing.Process(target=process_pdf, args=(pdf, root_path, temp_path, output_root))
    #     p.start()
    #     processes.append(p)
    
    #     # 控制并发进程数量
    #     if len(processes) >= max_processes or i == len(pdf_list) - 1:
    #         for p in processes:
    #             p.join()
    #         processes = []


    