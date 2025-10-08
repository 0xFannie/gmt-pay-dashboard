#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMT Pay 数据自动刷新脚本
每30分钟自动刷新链上数据和VIP用户分析
"""

import time
import subprocess
import os
from datetime import datetime
import sys

def log(message):
    """输出日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def refresh_data():
    """刷新数据"""
    try:
        log("开始刷新数据...")
        
        # 1. 刷新链上数据（通过streamlit的缓存机制自动刷新）
        log("✓ 链上数据将在用户访问时自动刷新（30分钟缓存）")
        
        # 2. 刷新VIP用户分析
        log("正在刷新VIP用户分析数据...")
        result = subprocess.run(
            [sys.executable, 'analyze_vip_users.py'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            log("✓ VIP用户分析数据刷新成功")
        else:
            log(f"✗ VIP用户分析刷新失败: {result.stderr[:200]}")
        
        log("数据刷新完成！")
        return True
        
    except Exception as e:
        log(f"✗ 数据刷新出错: {str(e)}")
        return False

def main():
    """主函数"""
    log("=" * 60)
    log("GMT Pay 数据自动刷新服务启动")
    log("刷新间隔: 30分钟")
    log("=" * 60)
    
    # 首次立即刷新
    refresh_data()
    
    # 每30分钟刷新一次
    refresh_interval = 30 * 60  # 30分钟
    
    while True:
        try:
            log(f"等待 {refresh_interval // 60} 分钟后下次刷新...")
            time.sleep(refresh_interval)
            refresh_data()
        except KeyboardInterrupt:
            log("收到停止信号，退出刷新服务")
            break
        except Exception as e:
            log(f"发生错误: {str(e)}")
            log("等待5分钟后重试...")
            time.sleep(300)

if __name__ == "__main__":
    main()

