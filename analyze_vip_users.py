#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析特权用户（Genesis NFT Holder & Legendary Achievement Holder）的购卡情况
"""

import sys
import io

# 强制UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import glob
from datetime import datetime

def load_vip_users():
    """加载所有周的特权用户名单，返回每周快照的地址集合"""
    print("正在加载特权用户名单（按周快照）...")
    
    # 存储每周的快照数据：{week_number: {'evm': set(), 'solana': set()}}
    weekly_snapshots = {}
    
    # 读取所有TSV文件
    tsv_files = glob.glob('nft-owners-*.tsv')
    print(f"找到 {len(tsv_files)} 个TSV文件")
    
    # 解析周数
    import re
    week_pattern = re.compile(r'(\d+)(st|nd|rd|th)\s+week')
    
    for file in sorted(tsv_files):
        # 提取周数
        match = week_pattern.search(file)
        if not match:
            continue
        week_num = int(match.group(1))
        
        print(f"  读取第{week_num}周快照: {file}...")
        
        if week_num not in weekly_snapshots:
            weekly_snapshots[week_num] = {'evm': set(), 'solana': set()}
        
        try:
            # 读取TSV文件，无表头
            df = pd.read_csv(file, sep='\t', header=None, names=['contract', 'chain', 'token_or_holder', 'holder_or_asset'])
            
            for _, row in df.iterrows():
                # 检查是否有空值
                if pd.isna(row['chain']) or pd.isna(row['holder_or_asset']):
                    continue
                    
                chain = str(row['chain']).lower().strip()
                
                if chain == 'sol':
                    # Solana链：第4列是holder地址
                    holder = str(row['holder_or_asset']).strip()
                    if len(holder) > 20:
                        weekly_snapshots[week_num]['solana'].add(holder)
                elif chain in ['pol', 'bnb', 'eth']:
                    # EVM链：第4列是holder地址
                    holder = str(row['holder_or_asset']).strip().lower()
                    if holder.startswith('0x') and len(holder) == 42:
                        weekly_snapshots[week_num]['evm'].add(holder)
        except Exception as e:
            print(f"  ⚠️  读取 {file} 时出错: {e}")
    
    # 统计总数（去重）
    all_evm = set()
    all_solana = set()
    for week_data in weekly_snapshots.values():
        all_evm.update(week_data['evm'])
        all_solana.update(week_data['solana'])
    
    print(f"\n✅ 加载完成:")
    print(f"   EVM地址（ETH/BNB/Polygon）: {len(all_evm)} 个")
    print(f"   Solana地址: {len(all_solana)} 个")
    print(f"   总计特权用户: {len(all_evm) + len(all_solana)} 个")
    print(f"   快照周数: {len(weekly_snapshots)} 周\n")
    
    return weekly_snapshots, all_evm, all_solana

def load_transaction_data():
    """加载GMT Pay交易数据"""
    print("正在加载GMT Pay交易数据...")
    
    cache_file = 'chain_data_cache.csv'
    try:
        df = pd.read_csv(cache_file)
        
        # 标准化地址格式
        df['From_Lower'] = df['From'].str.lower().str.strip()
        
        # 确保DateTime是datetime类型
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        df['Date'] = df['DateTime'].dt.date
        
        print(f"✅ 加载 {len(df)} 条交易记录\n")
        return df
    except Exception as e:
        print(f"❌ 加载交易数据失败: {e}")
        return pd.DataFrame()

def determine_card_value(amount):
    """根据支付金额确定卡片面值"""
    CARD_DENOMINATIONS = {
        '25 USD': {'min': 24.5, 'max': 27, 'value': 25},
        '50 USD': {'min': 48, 'max': 54, 'value': 50},
        '100 USD': {'min': 98, 'max': 107, 'value': 100},
        '200 USD': {'min': 195, 'max': 212, 'value': 200},
        '300 USD': {'min': 295, 'max': 318, 'value': 300}
    }
    
    for card_name, range_info in CARD_DENOMINATIONS.items():
        if range_info['min'] <= amount <= range_info['max']:
            return range_info['value']
    return 0

def get_snapshot_week_for_datetime(dt):
    """根据交易时间判断属于哪一周的快照有效期"""
    # 首次快照：2025-07-21 08:00 UTC
    # 每周快照一次，有效期7天
    first_snapshot = pd.to_datetime('2025-07-21 08:00:00')
    
    if dt < first_snapshot:
        return 0  # 活动前
    
    # 计算距离首次快照的天数
    days_diff = (dt - first_snapshot).total_seconds() / 86400
    week_num = int(days_diff // 7) + 1  # 第几周
    
    return week_num

def analyze_vip_purchases():
    """分析特权用户的购卡情况"""
    
    # 1. 加载特权用户名单（按周）
    weekly_snapshots, evm_addresses, solana_addresses = load_vip_users()
    
    # 2. 加载交易数据
    df_tx = load_transaction_data()
    
    if df_tx.empty:
        print("❌ 无交易数据可分析")
        return
    
    # 3. 筛选出特权用户的交易
    print("正在匹配特权用户的购卡记录...")
    
    # EVM链交易（Ethereum, BNB Chain, Polygon）
    evm_chains = ['Ethereum', 'BNB Chain', 'Polygon']
    df_evm_vip = df_tx[
        (df_tx['Chain'].isin(evm_chains)) & 
        (df_tx['From_Lower'].isin(evm_addresses))
    ].copy()
    
    # Solana链交易
    df_sol_vip = df_tx[
        (df_tx['Chain'] == 'Solana') & 
        (df_tx['From'].isin(solana_addresses))
    ].copy()
    
    # 合并所有特权用户的交易
    df_vip = pd.concat([df_evm_vip, df_sol_vip], ignore_index=True)
    
    # 只保留inflow交易（转入交易）
    df_vip = df_vip[df_vip['Direction'] == 'inflow'].copy()
    
    # 只保留使用支持代币的交易（USDC, USDT, GGUSD）
    supported_tokens = ['USDC', 'USDT', 'GGUSD']
    df_vip = df_vip[df_vip['Asset'].isin(supported_tokens)].copy()
    
    # 添加卡片面值
    df_vip['Card_Value'] = df_vip['Amount'].apply(determine_card_value)
    
    # 只保留有效的卡片交易
    df_vip_valid = df_vip[df_vip['Card_Value'] > 0].copy()
    
    # 判断购卡时属于哪一周的快照期
    df_vip_valid['Snapshot_Week'] = df_vip_valid['DateTime'].apply(get_snapshot_week_for_datetime)
    
    # 检查用户在购卡时是否在该周快照名单中
    def check_in_snapshot(row):
        week = row['Snapshot_Week']
        if week == 0 or week not in weekly_snapshots:
            return False
        
        if row['Chain'] in ['Ethereum', 'BNB Chain', 'Polygon']:
            return row['From_Lower'] in weekly_snapshots[week]['evm']
        elif row['Chain'] == 'Solana':
            return row['From'] in weekly_snapshots[week]['solana']
        return False
    
    df_vip_valid['In_Snapshot'] = df_vip_valid.apply(check_in_snapshot, axis=1)
    
    # 计算折扣情况
    # 正确的折扣逻辑（研发需求文档）：
    # 原价 = 卡片面值 + (卡片面值 × 3% + 1)
    # 折扣后 = 卡片面值 + (卡片面值 × 3% + 1) × (1 - 30%)
    # 特例：$25卡片固定$1手续费，不参与折扣
    #
    # 示例：
    # - 100 USD: $100 + $4 × 0.7 = $102.8
    # - 200 USD: $200 + $7 × 0.7 = $204.9
    # - 25 USD: $25 + $1 = $26 (固定，不打折)
    
    df_vip_valid['Original_Fee'] = df_vip_valid['Card_Value'] * 0.03 + 1  # 原始开卡费
    df_vip_valid['Normal_Payment'] = df_vip_valid['Card_Value'] + df_vip_valid['Original_Fee']  # 普通用户应付（原价）
    
    # 特权用户折扣计算（$25卡不参与折扣）
    def calculate_vip_payment(row):
        if row['Card_Value'] == 25:
            return 25 + 1  # $25卡固定$1手续费
        else:
            return row['Card_Value'] + row['Original_Fee'] * 0.70  # 其他卡享受30%折扣
    
    # 活动开始日期：2025年7月21日
    activity_start_date = pd.to_datetime('2025-07-21').date()
    df_vip_valid['Is_After_Activity'] = df_vip_valid['Date'] >= activity_start_date
    
    df_vip_valid['Expected_Payment'] = df_vip_valid.apply(calculate_vip_payment, axis=1)
    df_vip_valid['VIP_Discount'] = df_vip_valid['Normal_Payment'] - df_vip_valid['Expected_Payment']  # 理论折扣金额
    df_vip_valid['Actual_Savings'] = df_vip_valid['Expected_Payment'] - df_vip_valid['Amount']  # 实际节省（正数=享受折扣，负数=多付了）
    
    # 折扣状态判断：综合考虑活动时间、快照名单、实付金额
    def determine_discount_status(row):
        if not row['Is_After_Activity']:
            return '⏸️活动前'  # 活动前不可能享受折扣
        elif not row['In_Snapshot']:
            return '❓不在快照'  # 购卡时不在有效快照名单中
        elif row['Actual_Savings'] >= -0.5:  # 容差0.5
            return '✅已享受'
        else:
            return '❌未享受'
    
    df_vip_valid['Discount_Status'] = df_vip_valid.apply(determine_discount_status, axis=1)
    
    print(f"✅ 匹配完成:")
    print(f"   特权用户购卡记录: {len(df_vip_valid)} 笔")
    print(f"   其中 EVM链: {len(df_vip_valid[df_vip_valid['Chain'].isin(evm_chains)])} 笔")
    print(f"   其中 Solana链: {len(df_vip_valid[df_vip_valid['Chain'] == 'Solana'])} 笔")
    print(f"   活动前(2025-07-21前): {len(df_vip_valid[~df_vip_valid['Is_After_Activity']])} 笔")
    print(f"   活动后(2025-07-21起): {len(df_vip_valid[df_vip_valid['Is_After_Activity']])} 笔")
    # 统计快照匹配情况
    activity_after = df_vip_valid[df_vip_valid['Is_After_Activity']]
    in_snapshot_count = len(activity_after[activity_after['In_Snapshot']])
    not_in_snapshot_count = len(activity_after[~activity_after['In_Snapshot']])
    
    print(f"\n📸 快照匹配情况（活动后）：")
    print(f"   ✅ 购卡时在有效快照期内: {in_snapshot_count} 笔 ({in_snapshot_count/len(activity_after)*100:.1f}%)")
    print(f"   ❌ 购卡时不在快照期内: {not_in_snapshot_count} 笔 ({not_in_snapshot_count/len(activity_after)*100:.1f}%)")
    print(f"\n⚠️  说明：")
    print(f"   - 快照每7天一次（首次：2025-07-21 08:00 UTC）")
    print(f"   - 只有在有效快照期内购卡才能享受折扣")
    print(f"   - 不在快照期的用户可能是在快照间隙购卡或已转让NFT\n")
    
    # 4. 按日期统计
    print("=" * 80)
    print("📊 特权用户购卡情况 - 按日统计")
    print("=" * 80)
    
    # 按日期和链分组统计
    daily_summary = df_vip_valid.groupby(['Date', 'Chain']).agg({
        'Card_Value': ['count', 'sum'],
        'Amount': 'sum',
        'Expected_Payment': 'sum',
        'VIP_Discount': 'sum'
    }).round(2)
    
    daily_summary.columns = ['卡片数量', '卡片总面值(USD)', '实付金额(USD)', '应付金额(USD)', '应享折扣(USD)']
    
    print(daily_summary.to_string())
    
    # 5. 按卡片面值统计
    print("\n" + "=" * 80)
    print("📊 特权用户购卡情况 - 按面值统计")
    print("=" * 80)
    
    card_value_summary = df_vip_valid.groupby('Card_Value').agg({
        'Card_Value': 'count',
        'Expected_Payment': 'mean',
        'Amount': 'mean',
        'VIP_Discount': 'mean'
    }).round(2)
    
    card_value_summary.columns = ['卡片数量', '应付(USD)', '实付(USD)', '应享折扣(USD)']
    card_value_summary.index.name = '卡片面值(USD)'
    
    print(card_value_summary.to_string())
    
    # 6. 保存详细数据到CSV
    output_file = 'vip_users_purchases.csv'
    df_vip_valid_export = df_vip_valid[[
        'DateTime', 'Date', 'Chain', 'From', 'Asset', 
        'Card_Value', 'Amount', 'Expected_Payment', 'Normal_Payment',
        'VIP_Discount', 'Actual_Savings', 'Snapshot_Week', 'In_Snapshot', 
        'Discount_Status', 'Is_After_Activity', 'TxHash'
    ]].sort_values('DateTime')
    
    # 重命名列名为英文
    df_vip_valid_export.columns = [
        'DateTime', 'Date', 'Chain', 'Wallet', 'Asset',
        'Card_Value', 'Actual_Paid', 'Expected_VIP', 'Normal_User',
        'VIP_Discount', 'Savings', 'Snapshot_Week', 'In_Snapshot',
        'Status', 'After_2025-07-21', 'TxHash'
    ]
    
    df_vip_valid_export.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 详细数据已保存到: {output_file}")
    
    # 分析折扣情况 - 活动前后对比
    df_before = df_vip_valid[~df_vip_valid['Is_After_Activity']]
    df_after = df_vip_valid[df_vip_valid['Is_After_Activity']]
    
    # 7. 保存活动后未享受折扣的用户清单
    if len(df_after) > 0:
        after_no = df_after[df_after['Discount_Status'] == '❌未享受']
        if len(after_no) > 0:
            missing_discount_file = 'vip_missing_discount_after_activity.csv'
            df_missing = after_no[[
                'DateTime', 'Date', 'Chain', 'From', 'Asset',
                'Card_Value', 'Amount', 'Expected_Payment', 'VIP_Discount', 'Actual_Savings', 'TxHash'
            ]].sort_values('DateTime')
            
            df_missing.columns = [
                'DateTime', 'Date', 'Chain', 'Wallet', 'Asset',
                'Card_Value', 'Actual_Paid', 'Should_Paid', 'Should_Discount', 'Overpaid', 'TxHash'
            ]
            
            df_missing.to_csv(missing_discount_file, index=False, encoding='utf-8-sig')
            print(f"⚠️  活动后未享受折扣的交易清单已保存到: {missing_discount_file}")
    
    # 8. 总结统计
    print("\n" + "=" * 80)
    print("📈 总体统计")
    print("=" * 80)
    
    # 计算唯一用户数
    evm_users = df_vip_valid[df_vip_valid['Chain'].isin(evm_chains)]['From_Lower'].nunique()
    sol_users = df_vip_valid[df_vip_valid['Chain'] == 'Solana']['From'].nunique()
    
    print(f"特权用户总数: {len(evm_addresses) + len(solana_addresses)} 人")
    print(f"有购卡记录的特权用户: {evm_users + sol_users} 人 (EVM: {evm_users}, Solana: {sol_users})")
    print(f"购卡总数: {len(df_vip_valid)} 张")
    print(f"卡片总面值: ${df_vip_valid['Card_Value'].sum():,.0f}")
    print(f"普通用户需付: ${df_vip_valid['Normal_Payment'].sum():,.2f}")
    print(f"特权用户应付: ${df_vip_valid['Expected_Payment'].sum():,.2f}")
    print(f"实际支付: ${df_vip_valid['Amount'].sum():,.2f}")
    print(f"应享VIP折扣: ${df_vip_valid['VIP_Discount'].sum():,.2f}")
    
    # 分析折扣情况 - 总体
    got_discount = df_vip_valid[df_vip_valid['Discount_Status'] == '✅已享受']
    no_discount = df_vip_valid[df_vip_valid['Discount_Status'] == '❌未享受']
    
    print(f"\n折扣情况分析（总体）:")
    print(f"  ✅ 已享受VIP折扣: {len(got_discount)} 笔 ({len(got_discount)/len(df_vip_valid)*100:.1f}%)")
    print(f"  ❌ 未享受VIP折扣: {len(no_discount)} 笔 ({len(no_discount)/len(df_vip_valid)*100:.1f}%)")
    
    if len(got_discount) > 0:
        print(f"  平均实际节省(已享受): ${got_discount['Actual_Savings'].mean():.2f}")
    if len(no_discount) > 0:
        print(f"  平均多付金额(未享受): ${-no_discount['Actual_Savings'].mean():.2f}")
    
    print(f"\n折扣情况分析（按活动时间分）:")
    print(f"\n📅 活动前（2025-07-21之前）:")
    if len(df_before) > 0:
        print(f"  总计: {len(df_before)} 笔")
        print(f"  说明: 活动尚未开始，所有交易均为正常全价购卡")
    
    print(f"\n📅 活动后（2025-07-21起）:")
    if len(df_after) > 0:
        after_got = df_after[df_after['Discount_Status'] == '✅已享受']
        after_no = df_after[df_after['Discount_Status'] == '❌未享受']
        after_not_in_snapshot = df_after[df_after['Discount_Status'] == '❓不在快照']
        
        print(f"  总计: {len(df_after)} 笔")
        print(f"  ✅ 已享受折扣: {len(after_got)} 笔 ({len(after_got)/len(df_after)*100:.1f}%)")
        print(f"  ❓ 不在快照期: {len(after_not_in_snapshot)} 笔 ({len(after_not_in_snapshot)/len(df_after)*100:.1f}%)")
        print(f"  ❌ 在快照但未享受: {len(after_no)} 笔 ({len(after_no)/len(df_after)*100:.1f}%)")
        
        if len(after_got) > 0:
            print(f"\n  平均节省(已享受): ${after_got['Actual_Savings'].mean():.2f}")
        
        if len(after_not_in_snapshot) > 0:
            print(f"\n  📝 不在快照期说明：")
            print(f"     这些用户在某周持有NFT，但购卡时不在有效快照期内")
            print(f"     这是正常情况，无需处理")
        
        if len(after_no) > 0:
            print(f"\n  ⚠️  在快照但未享受折扣：")
            print(f"     这{len(after_no)}笔交易在快照期内但未享受折扣")
            print(f"     平均多付: ${-after_no['Actual_Savings'].mean():.2f}")
            print(f"     需要检查系统折扣识别问题！")
    
    print("=" * 80)

if __name__ == "__main__":
    analyze_vip_purchases()

