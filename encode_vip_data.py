#!/usr/bin/env python3
"""
VIP数据Base64编码脚本
用于生成Streamlit Secrets中使用的Base64编码VIP数据
"""

import pandas as pd
import base64
import os
from io import StringIO

def encode_vip_data():
    """将VIP用户购卡数据编码为Base64格式"""
    
    # 检查VIP数据文件是否存在
    vip_file = 'vip_users_purchases.csv'
    if not os.path.exists(vip_file):
        print(f"错误: 找不到VIP数据文件 {vip_file}")
        return None
    
    try:
        # 读取VIP数据
        df = pd.read_csv(vip_file)
        print(f"成功读取VIP数据: {len(df)} 条记录")
        
        # 转换为CSV字符串
        csv_string = df.to_csv(index=False)
        
        # Base64编码
        encoded_data = base64.b64encode(csv_string.encode('utf-8')).decode('utf-8')
        
        # 保存到文件
        output_file = 'vip_data_encoded.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encoded_data)
        
        print(f"Base64编码完成，保存到: {output_file}")
        print(f"编码后数据长度: {len(encoded_data)} 字符")
        
        # 显示前100个字符作为预览
        print(f"编码数据预览: {encoded_data[:100]}...")
        
        return encoded_data
        
    except Exception as e:
        print(f"编码过程中出错: {e}")
        return None

def decode_vip_data(encoded_data):
    """解码Base64数据并验证"""
    try:
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        df = pd.read_csv(StringIO(decoded_data))
        print(f"解码验证成功: {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"解码验证失败: {e}")
        return None

if __name__ == "__main__":
    print("=== VIP数据Base64编码工具 ===")
    
    # 编码数据
    encoded_data = encode_vip_data()
    
    if encoded_data:
        print("\n=== 解码验证 ===")
        # 验证解码
        decoded_df = decode_vip_data(encoded_data)
        
        if decoded_df is not None:
            print("\n=== 使用说明 ===")
            print("1. 将生成的Base64数据复制到Streamlit Secrets中")
            print("2. 在Streamlit Cloud的Secrets管理中添加:")
            print("   VIP_DATA_BASE64 = '你的Base64编码数据'")
            print("3. 这样可以在不暴露VIP用户地址的情况下部署应用")
        else:
            print("解码验证失败，请检查数据完整性")
    else:
        print("编码失败，请检查VIP数据文件")
