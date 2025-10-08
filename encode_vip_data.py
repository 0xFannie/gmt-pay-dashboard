#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将VIP数据文件编码为Base64，用于Streamlit Secrets
运行后将输出复制到 Streamlit Cloud -> Settings -> Secrets
"""

import base64
import os

def encode_file_to_base64(file_path):
    """将文件编码为Base64字符串"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return None
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    encoded = base64.b64encode(file_content).decode('utf-8')
    return encoded

if __name__ == "__main__":
    vip_file = 'vip_users_purchases.csv'
    
    print("VIP Data File Base64 Encoding Tool\n")
    
    encoded_data = encode_file_to_base64(vip_file)
    
    if encoded_data:
        # 计算大小
        size_kb = len(encoded_data) / 1024
        print(f"Success! Encoded size: {size_kb:.2f} KB")
        print(f"\n{'='*60}")
        print("Copy below content to Streamlit Cloud Secrets:")
        print(f"{'='*60}\n")
        print(f'VIP_DATA_BASE64 = """\n{encoded_data}\n"""')
        print(f"\n{'='*60}")
        
        if size_kb > 500:
            print("\nWarning: File is large, consider cloud storage solution")
        
        # 保存到文件
        with open('vip_data_encoded.txt', 'w', encoding='utf-8') as f:
            f.write(encoded_data)
        print(f"\nEncoded data also saved to: vip_data_encoded.txt")
    else:
        print("Encoding failed")

