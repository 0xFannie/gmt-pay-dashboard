import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
import os
from chain_data_fetcher import GMTPayDataFetcher

# 链品牌色配置 (官方品牌色)
CHAIN_COLORS = {
    'ethereum': {
        'color': '#627EEA',  # 以太坊蓝
        'bg': 'rgba(98, 126, 234, 0.1)', 
        'border': 'rgba(98, 126, 234, 0.3)'
    },
    'bnb chain': {
        'color': '#F3BA2F',  # 币安金色
        'bg': 'rgba(243, 186, 47, 0.1)', 
        'border': 'rgba(243, 186, 47, 0.3)'
    },
    'polygon': {
        'color': '#8247E5',  # Polygon紫色
        'bg': 'rgba(130, 71, 229, 0.1)', 
        'border': 'rgba(130, 71, 229, 0.3)'
    },
    'solana': {
        'color': '#14F195',  # Solana青绿色
        'gradient': 'linear-gradient(135deg, #9945FF 0%, #14F195 100%)',  # Solana渐变
        'bg': 'rgba(20, 241, 149, 0.1)', 
        'border': 'rgba(20, 241, 149, 0.3)'
    }
}

CHAIN_NAMES = {
    'ethereum': 'Ethereum',
    'bsc': 'BNB Chain',
    'polygon': 'Polygon',
    'solana': 'Solana'
}

def get_chain_color_map(chains):
    """为给定的链列表生成颜色映射"""
    color_map = {}
    for chain in chains:
        chain_lower = chain.lower()
        # 尝试精确匹配和模糊匹配
        if chain_lower in CHAIN_COLORS:
            color_map[chain] = CHAIN_COLORS[chain_lower]['color']
        elif 'bnb' in chain_lower or 'bsc' in chain_lower:
            color_map[chain] = CHAIN_COLORS['bnb chain']['color']
        elif 'polygon' in chain_lower:
            color_map[chain] = CHAIN_COLORS['polygon']['color']
        elif 'ethereum' in chain_lower or 'eth' in chain_lower:
            color_map[chain] = CHAIN_COLORS['ethereum']['color']
        elif 'solana' in chain_lower or 'sol' in chain_lower:
            color_map[chain] = CHAIN_COLORS['solana']['color']
        else:
            color_map[chain] = '#5B93FF'  # 默认蓝色
    return color_map

# 多语言文本配置
TRANSLATIONS = {
    'zh': {
        # 页面标题和基本信息
        'page_title': '💳 GMT Pay 数据看板',
        'product_website': '产品官网',
        'collection_address': '收款地址',
        'refund_address': '注销返还地址',
        'data_source': '数据源',
        'real_time': '实时从区块链抓取',
        'auto_refresh': '自动刷新',
        'every_30min': '每30分钟',
        
        # 促销活动
        'promo_title': '促销活动',
        'promo_desc': '用户主动注销卡片时,无论卡内余额多少,系统将自动返还 50% 余额作为 GGUSD 奖励至用户 Polygon 钱包',
        'refund_addr_label': '返还地址',
        
        # 侧边栏
        'sidebar_title': '⚙️ 筛选条件',
        'date_range': '📅 日期范围',
        'start_date': '开始日期',
        'end_date': '结束日期',
        'chain_filter': '🔗 区块链筛选',
        'all_chains': '全部链',
        'asset_filter': '💰 代币筛选',
        'all_assets': '全部代币',
        'card_value_filter': '💳 卡面值筛选',
        'all_values': '全部面值',
        'refresh_data': '🔄 刷新数据',
        'language_switch': '🌐 语言切换',
        
        # 核心指标
        'core_metrics': '📊 核心指标',
        'total_transactions': '总交易笔数',
        'total_cards': '总开卡数量',
        'total_revenue': '总实际收入',
        'avg_transaction': '平均交易金额',
        'total_fees': '总手续费收入',
        'avg_fee_rate': '平均手续费率',
        
        # 各链销售概览
        'chain_overview': '🌐 1. 各链销售概览',
        'chain_card_sales': '各链卡片销量',
        'chain_sales_ratio': '各链卡片销量占比',
        'chain_revenue': '各链实际收入',
        'chain_revenue_ratio': '各链收入占比',
        'chain_detailed_stats': '📊 各链详细统计',
        'chain': '链',
        'card_count': '卡片数量',
        'card_value_sum': '卡面值总和',
        'actual_revenue': '实际收入',
        'fee_income': '手续费收入',
        'avg_fee_rate_col': '平均手续费率',
        
        # 卡面值分析
        'card_value_analysis': '💳 2. 卡面值分析',
        'card_value_sales': '各卡面值销量',
        'card_value_sales_ratio': '卡面值销量占比',
        'card_value_revenue': '各卡面值收入',
        'card_value_revenue_ratio': '卡面值收入占比',
        'card_value': '卡面值',
        'count': '数量',
        'amount': '金额',
        
        # 代币使用分析
        'asset_analysis': '💰 3. 代币使用分析',
        'asset_sales': '各代币交易笔数',
        'asset_revenue': '各代币收入',
        'asset_usage_ratio': '各代币使用占比',
        'asset_chain_distribution': '🌐 各代币在不同链上的分布',
        'transaction_count': '交易笔数',
        'revenue_amount': '收入金额',
        'asset': '代币',
        
        # 手续费分析
        'fee_analysis': '💸 4. 手续费分析',
        'fee_rate_distribution': '手续费率分布',
        'fee_rate': '手续费率 (%)',
        'transaction_quantity': '交易数量',
        'min_fee_rate': '最低手续费率',
        'max_fee_rate': '最高手续费率',
        'median_fee_rate': '中位数手续费率',
        'chain_avg_fee_rate': '各链平均手续费率',
        
        # VIP用户分析
        'vip_analysis': '🎖️ 5. NFT持有者折扣分析',
        'vip_summary': 'NFT持有者购卡概览',
        'vip_total_users': '特权用户总数',
        'vip_purchased_users': '有购卡记录',
        'vip_total_cards': '购卡总数',
        'vip_discount_rate': '平均折扣享受率',
        'vip_snapshot_match': '📸 快照匹配情况（活动后）',
        'vip_in_snapshot': '在快照期内购卡',
        'vip_not_in_snapshot': '不在快照期',
        'vip_discount_status': '✅ 折扣享受情况',
        'vip_enjoyed': '已享受折扣',
        'vip_not_enjoyed': '在快照但未享受',
        'vip_by_chain': '📊 各链特权用户购卡情况',
        'vip_by_card_value': '💳 各面值购卡情况',
        'vip_insights': '💡 Insights Summary',
        'vip_activity_note': '注：NFT持有者30%折扣活动于2025年7月21日开始，每7天快照一次',
        
        # 原始交易数据
        'raw_transaction_data': '📋 6. 原始交易数据',
        'filtered_results': '当前筛选结果',
        'records': '条记录',
        'download_data': '📥 下载交易数据',
        'datetime': '时间',
        'txhash': '交易哈希',
        'from': '发送地址',
        'direction': '方向',
        'fee': '手续费',
        'fee_percentage': '手续费率(%)',
        
        # 卡片注销返还数据
        'refund_data': '💰 卡片注销返还数据',
        'total_refunds': '总返还笔数',
        'total_refund_amount': '总返还金额',
        'avg_refund': '平均返还金额',
        'max_refund': '最大返还金额',
        'refund_trend': '📈 返还趋势',
        'daily_refunds': '每日返还笔数',
        'daily_amount': '每日返还金额',
        'refund_distribution': '📊 返还金额分布',
        'monthly_stats': '📅 月度统计',
        'month': '月份',
        'refund_details': '📋 返还明细',
        'download_refund_data': '📥 下载返还数据',
        'no_refund_data': '暂无注销返还数据',
        
        # 页脚
        'footer_title': '💳 GMT Pay 数据看板',
        'supported_chains': '🔗 支持链',
        'supported_tokens': '💰 支持代币',
        
        # 其他
        'transaction': '笔',
        'cards': '张',
        'total': '总计',
    },
    'en': {
        # Page Title and Basic Info
        'page_title': '💳 GMT Pay Dashboard',
        'product_website': 'Product Website',
        'collection_address': 'Collection Address',
        'refund_address': 'Refund Address',
        'data_source': 'Data Source',
        'real_time': 'Real-time from blockchain',
        'auto_refresh': 'Auto Refresh',
        'every_30min': 'Every 30 minutes',
        
        # Promotional Activity
        'promo_title': 'Promotional Activity',
        'promo_desc': 'When users voluntarily cancel their cards, the system automatically refunds 50% of the remaining balance as GGUSD rewards to their Polygon wallet, regardless of the balance amount',
        'refund_addr_label': 'Refund Address',
        
        # Sidebar
        'sidebar_title': '⚙️ Filters',
        'date_range': '📅 Date Range',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'chain_filter': '🔗 Blockchain Filter',
        'all_chains': 'All Chains',
        'asset_filter': '💰 Token Filter',
        'all_assets': 'All Tokens',
        'card_value_filter': '💳 Card Value Filter',
        'all_values': 'All Values',
        'refresh_data': '🔄 Refresh Data',
        'language_switch': '🌐 Language',
        
        # Core Metrics
        'core_metrics': '📊 Core Metrics',
        'total_transactions': 'Total Transactions',
        'total_cards': 'Total Cards',
        'total_revenue': 'Total Revenue',
        'avg_transaction': 'Avg Transaction',
        'total_fees': 'Total Fees',
        'avg_fee_rate': 'Avg Fee Rate',
        
        # Chain Sales Overview
        'chain_overview': '🌐 1. Chain Sales Overview',
        'chain_card_sales': 'Card Sales by Chain',
        'chain_sales_ratio': 'Card Sales Ratio by Chain',
        'chain_revenue': 'Revenue by Chain',
        'chain_revenue_ratio': 'Revenue Ratio by Chain',
        'chain_detailed_stats': '📊 Detailed Chain Statistics',
        'chain': 'Chain',
        'card_count': 'Card Count',
        'card_value_sum': 'Card Value Sum',
        'actual_revenue': 'Actual Revenue',
        'fee_income': 'Fee Income',
        'avg_fee_rate_col': 'Avg Fee Rate',
        
        # Card Value Analysis
        'card_value_analysis': '💳 2. Card Value Analysis',
        'card_value_sales': 'Sales by Card Value',
        'card_value_sales_ratio': 'Sales Ratio by Card Value',
        'card_value_revenue': 'Revenue by Card Value',
        'card_value_revenue_ratio': 'Revenue Ratio by Card Value',
        'card_value': 'Card Value',
        'count': 'Count',
        'amount': 'Amount',
        
        # Asset Usage Analysis
        'asset_analysis': '💰 3. Asset Usage Analysis',
        'asset_sales': 'Transactions by Asset',
        'asset_revenue': 'Revenue by Asset',
        'asset_usage_ratio': 'Asset Usage Ratio',
        'asset_chain_distribution': '🌐 Asset Distribution by Chain',
        'transaction_count': 'Transaction Count',
        'revenue_amount': 'Revenue Amount',
        'asset': 'Asset',
        
        # Fee Analysis
        'fee_analysis': '💸 4. Fee Analysis',
        'fee_rate_distribution': 'Fee Rate Distribution',
        'fee_rate': 'Fee Rate (%)',
        'transaction_quantity': 'Transaction Quantity',
        'min_fee_rate': 'Min Fee Rate',
        'max_fee_rate': 'Max Fee Rate',
        'median_fee_rate': 'Median Fee Rate',
        'chain_avg_fee_rate': 'Avg Fee Rate by Chain',
        
        # VIP User Analysis
        'vip_analysis': '🎖️ 5. NFT Holder Discount Analysis',
        'vip_summary': 'NFT Holder Purchase Overview',
        'vip_total_users': 'Total VIP Users',
        'vip_purchased_users': 'Users with Purchases',
        'vip_total_cards': 'Total Cards Purchased',
        'vip_discount_rate': 'Avg Discount Rate',
        'vip_snapshot_match': '📸 Snapshot Match (After Activity)',
        'vip_in_snapshot': 'In Snapshot Period',
        'vip_not_in_snapshot': 'Not in Snapshot',
        'vip_discount_status': '✅ Discount Status',
        'vip_enjoyed': 'Enjoyed Discount',
        'vip_not_enjoyed': 'In Snapshot but Not Enjoyed',
        'vip_by_chain': '📊 VIP Purchases by Chain',
        'vip_by_card_value': '💳 VIP Purchases by Card Value',
        'vip_insights': '💡 Insights Summary',
        'vip_activity_note': 'Note: NFT holder 30% discount activity started on July 21, 2025, with snapshots every 7 days',
        
        # Raw Transaction Data
        'raw_transaction_data': '📋 6. Raw Transaction Data',
        'filtered_results': 'Current Filtered Results',
        'records': 'records',
        'download_data': '📥 Download Transaction Data',
        'datetime': 'DateTime',
        'txhash': 'TxHash',
        'from': 'From',
        'direction': 'Direction',
        'fee': 'Fee',
        'fee_percentage': 'Fee Rate(%)',
        
        # Card Cancellation Refund Data
        'refund_data': '💰 Card Cancellation Refund Data',
        'total_refunds': 'Total Refunds',
        'total_refund_amount': 'Total Refund Amount',
        'avg_refund': 'Avg Refund',
        'max_refund': 'Max Refund',
        'refund_trend': '📈 Refund Trend',
        'daily_refunds': 'Daily Refunds',
        'daily_amount': 'Daily Amount',
        'refund_distribution': '📊 Refund Amount Distribution',
        'monthly_stats': '📅 Monthly Statistics',
        'month': 'Month',
        'refund_details': '📋 Refund Details',
        'download_refund_data': '📥 Download Refund Data',
        'no_refund_data': 'No refund data available',
        
        # Footer
        'footer_title': '💳 GMT Pay Dashboard',
        'supported_chains': '🔗 Supported Chains',
        'supported_tokens': '💰 Supported Tokens',
        
        # Others
        'transaction': '',
        'cards': '',
        'total': 'Total',
    }
}

def get_text(key, lang='zh'):
    """获取指定语言的文本"""
    return TRANSLATIONS.get(lang, TRANSLATIONS['zh']).get(key, key)

# 页面配置
st.set_page_config(
    page_title="GMT Pay 卡片销售数据看板 (动态链上数据)",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Tailwind-inspired Modern UI System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    /* === Base & Layout === */
    .stApp {
        background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* === Metric Cards (tw: card, rounded-xl, shadow-sm) === */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        transform: translateY(-2px);
        border-color: #cbd5e1;
    }
    
    [data-testid="stMetricValue"] {
        color: #0f172a;
        font-size: 1.875rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        line-height: 2.25rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        line-height: 1.25rem;
    }
    
    [data-testid="stMetricDelta"] {
        color: #10b981 !important;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    /* === Typography (tw: text-4xl, font-bold) === */
    h1 {
        color: #0f172a !important;
        font-size: 2.25rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
        margin-bottom: 1.5rem !important;
        line-height: 2.5rem !important;
    }
    
    h2 {
        color: #1e293b !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        line-height: 2rem !important;
    }
    
    h3 {
        color: #334155 !important;
        font-size: 1.125rem !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
        line-height: 1.75rem !important;
    }
    
    /* === Charts (tw: bg-white, rounded-lg, shadow) === */
    [data-testid="stPlotlyChart"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.25rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    }
    
    .js-plotly-plot {
        border-radius: 0.5rem;
        overflow: visible !important;
    }
    
    .js-plotly-plot .plotly {
        overflow: visible !important;
    }
    
    /* === Buttons (tw: bg-blue-600, hover:bg-blue-700) === */
    .stButton>button {
        background: linear-gradient(to bottom right, #3b82f6, #2563eb);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.625rem 1.25rem;
        font-weight: 600;
        font-size: 0.875rem;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.025em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(to bottom right, #2563eb, #1d4ed8);
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        transform: translateY(-1px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    /* === Sidebar (tw: bg-white, border-r) === */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stSidebar"] label {
        color: #475569 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }
    
    /* === Data Tables (tw: divide-y, rounded-lg) === */
    [data-testid="stDataFrame"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        overflow: hidden;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    .dataframe thead tr th {
        background: #f8fafc !important;
        color: #475569 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em;
        border-bottom: 2px solid #e2e8f0 !important;
        padding: 0.75rem 1rem !important;
    }
    
    .dataframe tbody tr:hover {
        background: #f8fafc !important;
    }
    
    /* === Expander (tw: bg-white, rounded-lg, border) === */
    [data-testid="stExpander"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    [data-testid="stExpander"] summary {
        color: #1e293b !important;
        font-weight: 600 !important;
        padding: 0.75rem 1rem !important;
        transition: background 0.15s ease;
    }
    
    [data-testid="stExpander"] summary:hover {
        background: #f8fafc !important;
    }
    
    /* === Form Inputs (tw: rounded-md, border-gray-300, focus:ring-blue-500) === */
    .stSelectbox label,
    .stMultiSelect label,
    .stDateInput label {
        color: #475569 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }
    
    .stDateInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border: 1px solid #cbd5e1 !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.875rem;
        transition: all 0.15s ease;
    }
    
    .stDateInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within,
    .stMultiSelect > div > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1) !important;
        outline: none;
    }
    
    /* === Radio Buttons (tw: inline-flex, rounded-lg) === */
    .stRadio > div {
        gap: 0.5rem;
    }
    
    .stRadio > div > label {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        transition: all 0.15s ease;
        cursor: pointer;
    }
    
    .stRadio > div > label:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }
    
    /* === Tabs (tw: tabs, tab-bordered) === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: #64748b;
        font-weight: 500;
        padding: 0.75rem 1rem;
        transition: all 0.15s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent;
        border-bottom-color: #3b82f6;
        color: #0f172a;
        font-weight: 600;
    }
    
    /* === Alert/Info Boxes (tw: alert, alert-info) === */
    .stAlert {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        padding: 1rem;
    }
    
    /* === Divider (tw: border-t, border-gray-200) === */
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 2rem 0;
    }
    
    /* === Code blocks (tw: bg-gray-100, rounded, font-mono) === */
    code {
        background: #f1f5f9;
        color: #334155;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# 标题和产品信息 (将在数据加载后显示)

# 业务常量
CARD_DENOMINATIONS = {
    '25 USD': {'min': 24.5, 'max': 27, 'value': 25},
    '50 USD': {'min': 48, 'max': 54, 'value': 50},
    '100 USD': {'min': 98, 'max': 107, 'value': 100},
    '200 USD': {'min': 195, 'max': 212, 'value': 200},
    '300 USD': {'min': 295, 'max': 318, 'value': 300}
}

SUPPORTED_CHAINS = ['Ethereum', 'BNB Chain', 'Polygon', 'Solana']
SUPPORTED_TOKENS = ['GGUSD', 'USDT', 'USDC', 'BUSD']

# 缓存数据加载函数
@st.cache_data(ttl=1800)  # 缓存30分钟
def load_chain_data(force_refresh=False):
    """从链上加载数据"""
    fetcher = GMTPayDataFetcher()
    
    # 尝试从缓存加载
    if not force_refresh:
        df = fetcher.load_from_cache(max_age_minutes=30)
        if df is not None and not df.empty:
            return df
    
    # 从链上抓取所有历史数据（设置足够大的天数）
    with st.spinner('正在从区块链抓取所有历史数据，请稍候...'):
        df = fetcher.fetch_all_chains(days=3650)  # 抓取最近10年的所有数据
        
        if not df.empty:
            # 保存到缓存
            fetcher.save_to_cache(df)
        
        return df

@st.cache_data(ttl=1800)  # 缓存30分钟
def load_refund_data(force_refresh=False):
    """加载注销返还数据 (Polygon 链 GGUSD outflow)"""
    from chain_data_fetcher import EtherscanFetcher
    
    # Polygon 链的注销返还地址
    refund_address = '0x6f724c70500d899883954a5ac2e6f38d25422f60'
    
    # 创建 Polygon fetcher
    fetcher = EtherscanFetcher('polygon')
    
    with st.spinner('正在获取注销返还数据...'):
        # 获取 outflow 数据
        df = fetcher.fetch_transactions(refund_address, days=3650, direction='outflow')
        
        # 只保留 GGUSD
        if not df.empty:
            df = df[df['Asset'] == 'GGUSD']
        
        return df

def determine_card_value(amount):
    """根据支付金额确定卡片面值"""
    for card_name, range_info in CARD_DENOMINATIONS.items():
        if range_info['min'] <= amount <= range_info['max']:
            return range_info['value']
    return 0  # 无法识别的金额

@st.cache_data(ttl=1800)  # 缓存30分钟
def load_vip_analysis():
    """加载VIP用户购卡分析数据"""
    vip_file = 'vip_users_purchases.csv'
    if not os.path.exists(vip_file):
        return None
    
    try:
        df = pd.read_csv(vip_file)
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        st.error(f"加载VIP数据失败: {e}")
        return None

def process_data(df):
    """处理数据，添加业务字段"""
    if df.empty:
        return df
    
    # 过滤异常值
    df = df[(df['Amount'] > 0) & (df['Amount'] < 10000)]
    
    # 添加卡片面值列
    df['Card_Value'] = df['Amount'].apply(determine_card_value)
    
    # 计算手续费
    df['Fee'] = df.apply(lambda row: row['Amount'] - row['Card_Value'] if row['Card_Value'] > 0 else 0, axis=1)
    df['Fee_Percentage'] = df.apply(lambda row: (row['Fee'] / row['Card_Value'] * 100) if row['Card_Value'] > 0 else 0, axis=1)
    
    return df

# 初始化session state中的语言设置
if 'language' not in st.session_state:
    st.session_state.language = 'zh'

# 侧边栏 - 语言选择器 (置顶)
st.sidebar.markdown("### 🌐 语言 / Language")
lang_options = {'中文': 'zh', 'English': 'en'}
selected_lang_display = st.sidebar.radio(
    "",
    options=list(lang_options.keys()),
    index=0 if st.session_state.language == 'zh' else 1,
    horizontal=True
)
st.session_state.language = lang_options[selected_lang_display]
lang = st.session_state.language

st.sidebar.markdown("---")

# 侧边栏控制
st.sidebar.header(get_text('sidebar_title', lang))

# 刷新按钮
if st.sidebar.button(get_text('refresh_data', lang), use_container_width=True):
    st.cache_data.clear()
    df_raw = load_chain_data(force_refresh=True)
    st.success("数据已刷新!")
else:
    df_raw = load_chain_data(force_refresh=False)

# 显示数据加载状态
if df_raw.empty:
    st.error("⚠️ 无法加载数据。请检查:")
    st.markdown("""
    1. 网络连接是否正常
    2. API Keys 是否已配置（参考 .env.example）
    3. 是否有交易记录
    
    **临时解决方案**: 如果链上数据获取失败，系统会尝试使用缓存数据。
    """)
    st.stop()

# 处理数据
df = process_data(df_raw)

if df.empty:
    st.warning("数据加载成功，但没有有效的交易记录")
    st.stop()

# 显示数据信息
cache_file = 'chain_data_cache.csv'
if os.path.exists(cache_file):
    cache_age = (datetime.now().timestamp() - os.path.getmtime(cache_file)) / 60
    if lang == 'zh':
    st.sidebar.info(f"📊 数据状态\n\n缓存时间: {cache_age:.1f} 分钟前\n\n总记录: {len(df)} 条")
    else:
        st.sidebar.info(f"📊 Data Status\n\nCached: {cache_age:.1f} min ago\n\nTotal records: {len(df)}")

# 过滤出有效卡片（能识别出面值的）
df_valid = df[df['Card_Value'] > 0].copy()

# 侧边栏 - 筛选器
st.sidebar.header("🔍 " + ("数据筛选" if lang == 'zh' else "Data Filters"))

# 日期范围筛选
min_date = df_valid['DateTime'].min()
max_date = df_valid['DateTime'].max()

date_range = st.sidebar.date_input(
    "选择日期范围" if lang == 'zh' else "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_valid[(df_valid['DateTime'].dt.date >= start_date) & (df_valid['DateTime'].dt.date <= end_date)]
else:
    df_filtered = df_valid

# 链筛选
selected_chains = st.sidebar.multiselect(
    "选择区块链" if lang == 'zh' else "Select Blockchain",
    options=[('全部' if lang == 'zh' else 'All')] + SUPPORTED_CHAINS,
    default=[('全部' if lang == 'zh' else 'All')]
)

all_text = '全部' if lang == 'zh' else 'All'
if all_text not in selected_chains and len(selected_chains) > 0:
    df_filtered = df_filtered[df_filtered['Chain'].isin(selected_chains)]

# 卡片面值筛选
card_values = st.sidebar.multiselect(
    "选择卡片面值" if lang == 'zh' else "Select Card Value",
    options=[all_text] + sorted(df_filtered['Card_Value'].unique()),
    default=[all_text]
)

if all_text not in card_values and len(card_values) > 0:
    df_filtered = df_filtered[df_filtered['Card_Value'].isin(card_values)]

# Asset 筛选
selected_assets = st.sidebar.multiselect(
    "选择支付代币" if lang == 'zh' else "Select Token",
    options=[all_text] + SUPPORTED_TOKENS,
    default=[all_text]
)

if all_text not in selected_assets and len(selected_assets) > 0:
    df_filtered = df_filtered[df_filtered['Asset'].isin(selected_assets)]

# 显示筛选后的数据统计
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 " + ("筛选结果" if lang == 'zh' else "Filter Results"))
st.sidebar.metric("卡片销售数量" if lang == 'zh' else "Card Sales", len(df_filtered))
st.sidebar.metric("卡片总面值" if lang == 'zh' else "Total Card Value", f"${df_filtered['Card_Value'].sum():,.0f}")
st.sidebar.metric("实际收入" if lang == 'zh' else "Actual Revenue", f"${df_filtered['Amount'].sum():,.2f}")
st.sidebar.metric("手续费收入" if lang == 'zh' else "Fee Income", f"${df_filtered['Fee'].sum():,.2f}")

# ===================== 主面板 =====================

# 标题和产品信息
st.title(get_text('page_title', lang))
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%); 
            border: 1px solid rgba(16, 185, 129, 0.3); 
            border-radius: 16px; 
            padding: 30px; 
            box-shadow: 0 8px 32px rgba(16, 185, 129, 0.1); 
            margin-bottom: 30px;">
<p style="color: #1a1a1a; font-size: 18px; margin: 0; line-height: 1.8;">
<strong style="color: #059669;">{get_text('product_website', lang)}</strong>: <a href="https://fsl.com/gmtpay" style="color: #10b981; text-decoration: none; font-weight: 600;">fsl.com/gmtpay</a><br><br>
<strong style="color: #059669;">{get_text('collection_address', lang)}</strong>:<br>
• EVM {get_text('chain', lang)}: <code style="background: rgba(16, 185, 129, 0.15); color: #1a1a1a; padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.3);">0x523ffC4D9782dC8af35664625fBB3e1d8e8ec6cb</code><br>
• Solana: <code style="background: rgba(16, 185, 129, 0.15); color: #1a1a1a; padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.3);">G7bMBQegH3RyRjt1QZu3o6BA2ZQQ7shdJ7zGrw7PwNEL</code><br><br>
<strong style="color: #059669;">{get_text('refund_address', lang)}</strong> (Polygon):<br>
• <code style="background: rgba(16, 185, 129, 0.15); color: #1a1a1a; padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.3);">0x6f724c70500d899883954a5ac2e6f38d25422f60</code><br><br>
⚡ <strong style="color: #059669;">{get_text('data_source', lang)}</strong>: <span style="color: #1a1a1a;">{get_text('real_time', lang)}</span> | 🔄 <strong style="color: #059669;">{get_text('auto_refresh', lang)}</strong>: <span style="color: #1a1a1a;">{get_text('every_30min', lang)}</span>
</p>
</div>
""", unsafe_allow_html=True)

# 核心指标
st.header(get_text('core_metrics', lang))

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_cards = len(df_filtered)
    st.metric(get_text('total_cards', lang), f"{total_cards:,} {get_text('cards', lang)}")

with col2:
    total_card_value = df_filtered['Card_Value'].sum()
    st.metric(get_text('card_value_sum', lang), f"${total_card_value:,.0f}")

with col3:
    total_revenue = df_filtered['Amount'].sum()
    st.metric(get_text('total_revenue', lang), f"${total_revenue:,.2f}")

with col4:
    total_fee = df_filtered['Fee'].sum()
    st.metric(get_text('total_fees', lang), f"${total_fee:,.2f}")

with col5:
    avg_fee_pct = df_filtered['Fee_Percentage'].mean()
    st.metric(get_text('avg_fee_rate', lang), f"{avg_fee_pct:.2f}%")

# 数据说明
if lang == 'zh':
    st.info("""
    **💡 关于开卡数量的说明**
    
    此处显示的开卡数量是基于**链上支付成功**的交易统计。如果BANO系统（卡片供应商）显示的开卡数量小于此处数据，这是正常现象。
    
    **原因：** 存在用户链上付款成功但业务系统开卡失败的情况，这些订单通常正在客服处理流程中。
    
    **常见失败原因：**
    - GMT Pay产品系统异常
    - BANO系统服务错误
    - 其他技术问题
    
    ⚠️ 链上数据 ≥ BANO系统开卡数 为正常情况
    """)
else:
    st.info("""
    **💡 About Card Issuance Count**
    
    The card count shown here is based on **successful on-chain payments**. If BANO system (card supplier) shows fewer cards than this data, it's normal.
    
    **Reason:** Some users' payments succeed on-chain but card issuance fails in the business system. These orders are typically being handled by customer service.
    
    **Common failure reasons:**
    - GMT Pay product system issues
    - BANO system service errors
    - Other technical problems
    
    ⚠️ On-chain data ≥ BANO system count is expected
    """)

st.markdown("---")

# 📑 目录导航
if lang == 'zh':
    toc_title = "📑 分析模块导航"
    toc_items = [
        ("🌐 各链销售概览", "#1"),
        ("💳 卡面值分析", "#2"),
        ("💰 代币使用分析", "#3"),
        ("💸 手续费分析", "#4"),
        ("🎖️ NFT持有者折扣分析", "#5"),
        ("💵 卡片注销返还GGUSD分析", "#refund"),
        ("📋 原始交易数据", "#6")
    ]
else:
    toc_title = "📑 Analysis Modules"
    toc_items = [
        ("🌐 Chain Sales Overview", "#1"),
        ("💳 Card Value Analysis", "#2"),
        ("💰 Token Usage Analysis", "#3"),
        ("💸 Fee Analysis", "#4"),
        ("🎖️ NFT Holder Discount Analysis", "#5"),
        ("💵 Card Cancellation Refund Analysis", "#refund"),
        ("📋 Raw Transaction Data", "#6")
    ]

toc_html = f"""
<div style="background: white; 
            border: 2px solid #e2e8f0; 
            border-radius: 16px; 
            padding: 24px 32px; 
            margin-bottom: 32px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
    <h3 style="color: #0f172a; font-size: 1.25rem; font-weight: 700; margin: 0 0 20px 0; 
               display: flex; align-items: center;">
        {toc_title}
    </h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px;">
"""

for item_text, item_id in toc_items:
    toc_html += f"""
        <a href="{item_id}" style="text-decoration: none;">
            <div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                        border: 1px solid #e2e8f0;
                        border-radius: 10px;
                        padding: 14px 18px;
                        transition: all 0.2s ease;
                        cursor: pointer;
                        color: #334155;
                        font-weight: 500;
                        font-size: 0.95rem;"
                 onmouseover="this.style.background='linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'; 
                             this.style.color='white'; 
                             this.style.borderColor='#3b82f6'; 
                             this.style.transform='translateY(-2px)';
                             this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.3)';"
                 onmouseout="this.style.background='linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'; 
                            this.style.color='#334155'; 
                            this.style.borderColor='#e2e8f0';
                            this.style.transform='translateY(0)';
                            this.style.boxShadow='none';">
                {item_text}
            </div>
        </a>
    """

toc_html += """
    </div>
</div>
"""

st.markdown(toc_html, unsafe_allow_html=True)

st.markdown("---")

# 1. 各链销售概览
st.markdown('<div id="1"></div>', unsafe_allow_html=True)
st.header(get_text('chain_overview', lang))

# 动态洞察摘要
chain_leader = df_filtered.groupby('Chain').size().idxmax()
chain_leader_pct = df_filtered.groupby('Chain').size().max() / len(df_filtered) * 100
total_chains = df_filtered['Chain'].nunique()

if lang == 'zh':
    st.markdown(f"""
    **📊 数据摘要与洞察**  
    共有 **{total_chains}** 条链产生销售。**{chain_leader}** 是销售主力，占总销量的 **{chain_leader_pct:.1f}%**。
    多链布局有效分散了风险，不同链的用户偏好为产品优化提供了方向。
    """)
else:
    st.markdown(f"""
    **📊 Data Summary & Insights**  
    **{total_chains}** chains generated sales. **{chain_leader}** leads with **{chain_leader_pct:.1f}%** of total sales.
    Multi-chain strategy effectively diversifies risk, and user preferences across chains provide optimization directions.
    """)

st.markdown("")

col1, col2 = st.columns(2)

with col1:
    st.subheader(get_text('chain_card_sales', lang))
    chain_cards = df_filtered.groupby('Chain').size().reset_index(name='Count')
    chain_cards = chain_cards.sort_values('Count', ascending=False)
    
    # 应用链品牌色
    chain_color_map = get_chain_color_map(chain_cards['Chain'].tolist())
    
    fig_chain_count = px.pie(
        chain_cards,
        values='Count',
        names='Chain',
        title=get_text('chain_sales_ratio', lang),
        color='Chain',
        color_discrete_map=chain_color_map
    )
    fig_chain_count.update_traces(textposition='inside', textinfo='percent+label+value')
    fig_chain_count.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
    )
    st.plotly_chart(fig_chain_count, use_container_width=True)
    
    st.dataframe(chain_cards, use_container_width=True)

with col2:
    st.subheader(get_text('chain_revenue', lang))
    chain_revenue = df_filtered.groupby('Chain')['Amount'].sum().reset_index()
    chain_revenue = chain_revenue.sort_values('Amount', ascending=False)
    
    # 应用链品牌色
    chain_color_map = get_chain_color_map(chain_revenue['Chain'].tolist())
    
    fig_chain_rev = px.pie(
        chain_revenue,
        values='Amount',
        names='Chain',
        title=get_text('chain_revenue_ratio', lang),
        color='Chain',
        color_discrete_map=chain_color_map
    )
    fig_chain_rev.update_traces(textposition='inside', textinfo='percent+label+value')
    fig_chain_rev.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
    )
    st.plotly_chart(fig_chain_rev, use_container_width=True)
    
    chain_revenue['Amount'] = chain_revenue['Amount'].apply(lambda x: f"${x:,.2f}")
    st.dataframe(chain_revenue, use_container_width=True)

# 各链详细统计表
st.subheader(get_text('chain_detailed_stats', lang))
chain_stats = df_filtered.groupby('Chain').agg({
    'Card_Value': ['count', 'sum'],
    'Amount': 'sum',
    'Fee': 'sum',
    'Fee_Percentage': 'mean'
}).round(2)

if lang == 'zh':
chain_stats.columns = ['卡片数量', '卡片总面值', '实际收入', '手续费收入', '平均手续费率(%)']
else:
    chain_stats.columns = ['Card Count', 'Card Value Sum', 'Actual Revenue', 'Fee Income', 'Avg Fee Rate(%)']
chain_stats = chain_stats.sort_values(chain_stats.columns[0], ascending=False)
st.dataframe(chain_stats, use_container_width=True)

# 时间趋势
st.subheader("📈 " + ("销售时间趋势" if lang == 'zh' else "Sales Trend Over Time"))
df_filtered['Date'] = df_filtered['DateTime'].dt.date
daily_stats = df_filtered.groupby(['Date', 'Chain']).agg({
    'Card_Value': 'count',
    'Amount': 'sum'
}).reset_index()
daily_stats.columns = ['Date', 'Chain', 'Cards_Count', 'Revenue']

fig_daily = go.Figure()

# 添加每日卡片销量
fig_daily.add_trace(go.Scatter(
    x=daily_stats.groupby('Date')['Cards_Count'].sum().index,
    y=daily_stats.groupby('Date')['Cards_Count'].sum().values,
    mode='lines+markers',
    name='Daily Card Sales' if lang == 'en' else '每日卡片销量',
    yaxis='y',
    line=dict(color='blue', width=2)
))

# 添加每日收入
fig_daily.add_trace(go.Scatter(
    x=daily_stats.groupby('Date')['Revenue'].sum().index,
    y=daily_stats.groupby('Date')['Revenue'].sum().values,
    mode='lines+markers',
    name='Daily Revenue (USD)' if lang == 'en' else '每日收入 (USD)',
    yaxis='y2',
    line=dict(color='green', width=2)
))

fig_daily.update_layout(
    title='Daily Sales Trend' if lang == 'en' else '每日销售趋势',
    xaxis=dict(title='Date' if lang == 'en' else '日期'),
    yaxis=dict(title='Card Sales' if lang == 'en' else '卡片销量', side='left'),
    yaxis2=dict(title='Revenue (USD)' if lang == 'en' else '收入 (USD)', side='right', overlaying='y'),
    hovermode='x unified',
    height=500
)

st.plotly_chart(fig_daily, use_container_width=True)

st.markdown("---")

# 2. 卡片面值分析
st.markdown('<div id="2"></div>', unsafe_allow_html=True)
st.header(get_text('card_value_analysis', lang))

# 动态洞察摘要
popular_value = df_filtered.groupby('Card_Value').size().idxmax()
popular_value_count = df_filtered.groupby('Card_Value').size().max()
popular_value_pct = popular_value_count / len(df_filtered) * 100
value_types = df_filtered['Card_Value'].nunique()

if lang == 'zh':
    st.markdown(f"""
    **📊 数据摘要与洞察**  
    共有 **{value_types}** 种面值卡片。**${popular_value:.0f}** 面值最受欢迎，售出 **{popular_value_count}** 张（占 **{popular_value_pct:.1f}%**）。
    用户偏好集中在中等面值，说明产品定价策略有效，满足了主流用户需求。
    """)
else:
    st.markdown(f"""
    **📊 Data Summary & Insights**  
    **{value_types}** card denominations available. **${popular_value:.0f}** is most popular with **{popular_value_count}** cards (**{popular_value_pct:.1f}%**).
    User preference for mid-range values indicates effective pricing strategy aligned with mainstream demand.
    """)

st.markdown("")

col1, col2 = st.columns(2)

with col1:
    st.subheader(get_text('card_value_sales', lang))
    card_value_counts = df_filtered.groupby('Card_Value').size().reset_index(name='Count')
    card_value_counts['Card_Value'] = card_value_counts['Card_Value'].astype(str) + ' USD'
    
    fig_cv_count = px.bar(
        card_value_counts,
        x='Card_Value',
        y='Count',
        title='Sales by Card Value' if lang == 'en' else '各面值卡片销量',
        text='Count',
        color='Card_Value',
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_cv_count.update_traces(texttemplate='%{text}', textposition='outside')
    fig_cv_count.update_layout(
        margin=dict(l=60, r=40, t=60, b=60),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        yaxis=dict(automargin=True)
    )
    st.plotly_chart(fig_cv_count, use_container_width=True)

with col2:
    st.subheader(get_text('card_value_revenue', lang))
    card_value_revenue = df_filtered.groupby('Card_Value')['Amount'].sum().reset_index()
    card_value_revenue['Card_Value'] = card_value_revenue['Card_Value'].astype(str) + ' USD'
    
    fig_cv_rev = px.bar(
        card_value_revenue,
        x='Card_Value',
        y='Amount',
        title='Revenue by Card Value' if lang == 'en' else '各面值卡片总收入',
        text='Amount',
        color='Card_Value',
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig_cv_rev.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_cv_rev.update_layout(
        margin=dict(l=60, r=40, t=60, b=60),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        yaxis=dict(automargin=True)
    )
    st.plotly_chart(fig_cv_rev, use_container_width=True)

# 各链各面值热力图
st.subheader("🔥 " + ("各链各面值销量热力图" if lang == 'zh' else "Heatmap: Sales by Chain & Card Value"))
heatmap_data = df_filtered.groupby(['Chain', 'Card_Value']).size().reset_index(name='Count')
heatmap_pivot = heatmap_data.pivot(index='Chain', columns='Card_Value', values='Count').fillna(0)

fig_heatmap = px.imshow(
    heatmap_pivot,
    labels=dict(
        x="Card Value (USD)" if lang == 'en' else "卡片面值 (USD)", 
        y="Blockchain" if lang == 'en' else "区块链", 
        color="Sales" if lang == 'en' else "销量"
    ),
    title='Sales Distribution by Chain & Card Value' if lang == 'en' else '各链各面值销量分布',
    color_continuous_scale='Blues',
    text_auto=True
)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# 3. 支付代币分析
st.markdown('<div id="3"></div>', unsafe_allow_html=True)
st.header(get_text('asset_analysis', lang))

# 动态洞察摘要
df_target_assets = df_filtered[df_filtered['Asset'].isin(SUPPORTED_TOKENS)]
if not df_target_assets.empty:
    top_token = df_target_assets.groupby('Asset').size().idxmax()
    top_token_pct = df_target_assets.groupby('Asset').size().max() / len(df_target_assets) * 100
    tokens_used = df_target_assets['Asset'].nunique()
    
    if lang == 'zh':
        st.markdown(f"""
        **📊 数据摘要与洞察**  
        用户使用了 **{tokens_used}** 种代币支付。**{top_token}** 是首选支付方式，占 **{top_token_pct:.1f}%**。
        代币使用分布反映了用户资产持有偏好，为流动性管理和代币支持策略提供依据。
        """)
    else:
        st.markdown(f"""
        **📊 Data Summary & Insights**  
        Users paid with **{tokens_used}** different tokens. **{top_token}** is preferred at **{top_token_pct:.1f}%**.
        Token usage distribution reflects user asset holdings and informs liquidity management strategy.
        """)
    
    st.markdown("")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader(get_text('asset_sales', lang))
    asset_counts = df_target_assets.groupby('Asset').size().reset_index(name='Count')
    asset_counts = asset_counts.sort_values('Count', ascending=False)
    
    fig_asset_count = px.bar(
        asset_counts,
        x='Asset',
        y='Count',
        title='Transactions by Asset' if lang == 'en' else '各代币交易笔数',
        text='Count',
        color='Asset',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_asset_count.update_traces(texttemplate='%{text}', textposition='outside')
    fig_asset_count.update_layout(
        margin=dict(l=60, r=40, t=60, b=60),
        yaxis=dict(automargin=True)
    )
    st.plotly_chart(fig_asset_count, use_container_width=True)

with col2:
    st.subheader(get_text('asset_revenue', lang))
    asset_revenue = df_target_assets.groupby('Asset')['Amount'].sum().reset_index()
    asset_revenue = asset_revenue.sort_values('Amount', ascending=False)
    
    fig_asset_rev = px.bar(
        asset_revenue,
        x='Asset',
        y='Amount',
        title='Revenue by Asset' if lang == 'en' else '各代币总收入',
        text='Amount',
        color='Asset',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_asset_rev.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_asset_rev.update_layout(
        margin=dict(l=60, r=40, t=60, b=60),
        yaxis=dict(automargin=True)
    )
    st.plotly_chart(fig_asset_rev, use_container_width=True)

with col3:
    st.subheader(get_text('asset_usage_ratio', lang))
    asset_percentage = df_target_assets.groupby('Asset').size().reset_index(name='Count')
    
    fig_asset_pie = px.pie(
        asset_percentage,
        values='Count',
        names='Asset',
        title='Asset Usage Ratio' if lang == 'en' else '各代币使用占比',
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig_asset_pie.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
    )
    st.plotly_chart(fig_asset_pie, use_container_width=True)

# 各代币在不同链上的分布
st.subheader(get_text('asset_chain_distribution', lang))

tab1, tab2 = st.tabs([get_text('transaction_count', lang), get_text('revenue_amount', lang)])

with tab1:
    asset_chain_counts = df_target_assets.groupby(['Asset', 'Chain']).size().reset_index(name='Count')
    
    # 应用链品牌色
    chain_color_map = get_chain_color_map(asset_chain_counts['Chain'].unique().tolist())
    
    fig_ac = px.bar(
        asset_chain_counts,
        x='Asset',
        y='Count',
        color='Chain',
        color_discrete_map=chain_color_map,
        title='Transactions by Asset & Chain' if lang == 'en' else '各代币在不同链上的交易笔数',
        barmode='group',
        text='Count'
    )
    fig_ac.update_traces(texttemplate='%{text}', textposition='outside')
    fig_ac.update_layout(
        margin=dict(l=60, r=40, t=60, b=80),
        yaxis=dict(automargin=True),
        xaxis=dict(automargin=True)
    )
    st.plotly_chart(fig_ac, use_container_width=True)
    
    pivot_ac = asset_chain_counts.pivot(index='Asset', columns='Chain', values='Count').fillna(0).astype(int)
    st.dataframe(pivot_ac, use_container_width=True)

with tab2:
    asset_chain_revenue = df_target_assets.groupby(['Asset', 'Chain'])['Amount'].sum().reset_index()
    
    # 应用链品牌色
    chain_color_map = get_chain_color_map(asset_chain_revenue['Chain'].unique().tolist())
    
    fig_acr = px.bar(
        asset_chain_revenue,
        x='Asset',
        y='Amount',
        color='Chain',
        color_discrete_map=chain_color_map,
        title='Revenue by Asset & Chain' if lang == 'en' else '各代币在不同链上的收入金额',
        barmode='group',
        text='Amount'
    )
    fig_acr.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_acr.update_layout(
        margin=dict(l=60, r=40, t=60, b=80),
        yaxis=dict(automargin=True),
        xaxis=dict(automargin=True)
    )
    st.plotly_chart(fig_acr, use_container_width=True)
    
    pivot_acr = asset_chain_revenue.pivot(index='Asset', columns='Chain', values='Amount').fillna(0)
    st.dataframe(pivot_acr.applymap(lambda x: f"${x:,.2f}"), use_container_width=True)

st.markdown("---")

# 4. 手续费分析
st.markdown('<div id="4"></div>', unsafe_allow_html=True)
st.header(get_text('fee_analysis', lang))

# 动态洞察摘要
total_fees_sum = df_filtered['Fee'].sum()
avg_fee = df_filtered['Fee'].mean()
avg_fee_rate = df_filtered['Fee_Percentage'].mean()

if lang == 'zh':
    st.markdown(f"""
    **📊 数据摘要与洞察**  
    累计手续费收入 **${total_fees_sum:,.2f}**，平均每笔 **${avg_fee:.2f}**，平均费率 **{avg_fee_rate:.2f}%**。
    手续费结构设计合理，在维持竞争力的同时保证了可持续的商业模式。不同面值的费率差异体现了规模效应。
    """)
else:
    st.markdown(f"""
    **📊 Data Summary & Insights**  
    Total fee revenue **${total_fees_sum:,.2f}**, average **${avg_fee:.2f}** per transaction, avg rate **{avg_fee_rate:.2f}%**.
    Fee structure balances competitiveness with sustainable business model. Rate variations across denominations reflect economies of scale.
    """)

st.markdown("")

col1, col2 = st.columns(2)

with col1:
    st.subheader(get_text('fee_rate_distribution', lang))
    fig_fee_dist = px.histogram(
        df_filtered,
        x='Fee_Percentage',
        nbins=50,
        title='Fee Rate Distribution' if lang == 'en' else '手续费率分布',
        labels={'Fee_Percentage': 'Fee Rate (%)' if lang == 'en' else '手续费率 (%)', 
                'count': 'Transaction Count' if lang == 'en' else '交易数量'},
        color_discrete_sequence=['lightblue']
    )
    fig_fee_dist.update_layout(bargap=0.1)
    st.plotly_chart(fig_fee_dist, use_container_width=True)
    
    st.metric(get_text('min_fee_rate', lang), f"{df_filtered['Fee_Percentage'].min():.2f}%")
    st.metric(get_text('max_fee_rate', lang), f"{df_filtered['Fee_Percentage'].max():.2f}%")
    st.metric(get_text('median_fee_rate', lang), f"{df_filtered['Fee_Percentage'].median():.2f}%")
    
    # 添加手续费率说明
    if lang == 'zh':
        st.info("""
        **💡 手续费率说明**
        
        手续费率 = 实际手续费 / 卡片面值 × 100%
        
        **示例：**
        - $25卡：$0.75手续费 = 3.00% 费率
        - $50卡：$2.50手续费 = 5.00% 费率
        - $100卡：$3.00手续费 = 3.00% 费率
        - $200卡：$6.00手续费 = 3.00% 费率
        
        ⚠️ 基础费率为卡面值的3%，较小面值卡片的费率相对较高。
        """)
    else:
        st.info("""
        **💡 Fee Rate Explanation**
        
        Fee Rate = Actual Fee / Card Face Value × 100%
        
        **Examples:**
        - $25 card: $0.75 fee = 3.00% rate
        - $50 card: $2.50 fee = 5.00% rate
        - $100 card: $3.00 fee = 3.00% rate
        - $200 card: $6.00 fee = 3.00% rate
        
        ⚠️ Base rate is 3% of card value. Smaller denominations have relatively higher rates.
        """)

with col2:
    st.subheader(get_text('chain_avg_fee_rate', lang))
    chain_fee = df_filtered.groupby('Chain')['Fee_Percentage'].mean().reset_index()
    chain_fee = chain_fee.sort_values('Fee_Percentage', ascending=False)
    
    # 应用链品牌色
    chain_color_map = get_chain_color_map(chain_fee['Chain'].tolist())
    
    fig_chain_fee = px.bar(
        chain_fee,
        x='Chain',
        y='Fee_Percentage',
        title='Avg Fee Rate by Chain' if lang == 'en' else '各链平均手续费率',
        color='Chain',
        color_discrete_map=chain_color_map,
        text='Fee_Percentage'
    )
    fig_chain_fee.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_chain_fee.update_layout(
        margin=dict(l=60, r=40, t=60, b=80),
        yaxis=dict(automargin=True),
        xaxis=dict(automargin=True)
    )
    st.plotly_chart(fig_chain_fee, use_container_width=True)

st.markdown("---")

# 5. NFT持有者折扣分析
st.markdown('<div id="5"></div>', unsafe_allow_html=True)
st.header(get_text('vip_analysis', lang))

# VIP名单来源说明
if lang == 'zh':
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(109, 40, 217, 0.05) 100%);
                border: 1px solid rgba(139, 92, 246, 0.3); 
                border-radius: 16px; 
                padding: 20px 24px; 
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1);">
    <p style="color: #1a1a1a; margin: 0; line-height: 1.8; font-size: 0.95rem;">
    <strong style="color: #7c3aed;">🎖️ VIP用户名单来源</strong><br>
    Genesis Holder + Morchi Achievement Legendary Holder 的每周钱包地址快照由 Cora 提供。<br>
    📊 <strong>截止今天的每周名单：</strong> <a href="https://www.notion.so/fsl-web3/Gensisi-Holder-Morchi-achievenment-legendary-holder-wallet-list-from-Cora-28595c775fea800fbbbedd6fda534108" target="_blank" style="color: #7c3aed; text-decoration: none; font-weight: 600;">查看 Notion 文档 →</a>
    </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(109, 40, 217, 0.05) 100%);
                border: 1px solid rgba(139, 92, 246, 0.3); 
                border-radius: 16px; 
                padding: 20px 24px; 
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1);">
    <p style="color: #1a1a1a; margin: 0; line-height: 1.8; font-size: 0.95rem;">
    <strong style="color: #7c3aed;">🎖️ VIP User List Source</strong><br>
    Weekly wallet snapshots of Genesis Holder + Morchi Achievement Legendary Holder are provided by Cora.<br>
    📊 <strong>Weekly lists up to today:</strong> <a href="https://www.notion.so/fsl-web3/Gensisi-Holder-Morchi-achievenment-legendary-holder-wallet-list-from-Cora-28595c775fea800fbbbedd6fda534108" target="_blank" style="color: #7c3aed; text-decoration: none; font-weight: 600;">View Notion Doc →</a>
    </p>
    </div>
    """, unsafe_allow_html=True)

# 加载VIP分析数据
df_vip = load_vip_analysis()

# 动态洞察摘要（在数据加载后添加）
if df_vip is not None and len(df_vip) > 0:
    activity_start_temp = pd.to_datetime('2025-07-21')
    df_vip_after_temp = df_vip[df_vip['After_2025-07-21'] == True]
    purchased_users_temp = df_vip['Wallet'].nunique()
    total_cards_temp = len(df_vip)
    
    if len(df_vip_after_temp) > 0:
        enjoyed_count_temp = len(df_vip_after_temp[df_vip_after_temp['Status'] == '✅已享受'])
        discount_rate_temp = enjoyed_count_temp / len(df_vip_after_temp) * 100
    else:
        discount_rate_temp = 0
    
    if lang == 'zh':
        st.markdown(f"""
        **📊 数据摘要与洞察**  
        共有 **{purchased_users_temp}** 名NFT持有者购买了 **{total_cards_temp}** 张卡片。活动启动后，**{discount_rate_temp:.1f}%** 的交易成功享受了折扣。
        VIP用户激活率体现了社区忠诚度，折扣政策有效促进了高价值用户的复购。未享受折扣的订单需关注技术实现和用户体验。
        """)
    else:
        st.markdown(f"""
        **📊 Data Summary & Insights**  
        **{purchased_users_temp}** NFT holders purchased **{total_cards_temp}** cards. Post-launch, **{discount_rate_temp:.1f}%** transactions received discounts.
        VIP activation rate reflects community loyalty. Discount policy effectively drives repeat purchases. Non-discounted orders warrant technical and UX review.
        """)
    
    st.markdown("")

if df_vip is not None and len(df_vip) > 0:
    # 活动开始日期
    activity_start = pd.to_datetime('2025-07-21')
    df_vip_after = df_vip[df_vip['After_2025-07-21'] == True]
    
    # 总体统计
    st.subheader(get_text('vip_summary', lang))
    
    # 计算总的VIP用户数（需要从TSV文件统计，这里用近似值）
    total_vip_users = 1777  # 从analyze_vip_users.py的结果
    purchased_users = df_vip['Wallet'].nunique()
    total_cards = len(df_vip)
    
    # 计算折扣享受率
    if len(df_vip_after) > 0:
        enjoyed_count = len(df_vip_after[df_vip_after['Status'] == '✅已享受'])
        discount_rate = enjoyed_count / len(df_vip_after) * 100
    else:
        discount_rate = 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(get_text('vip_total_users', lang), f"{total_vip_users:,}")
    with col2:
        st.metric(get_text('vip_purchased_users', lang), f"{purchased_users:,}")
    with col3:
        st.metric(get_text('vip_total_cards', lang), f"{total_cards:,}")
    with col4:
        st.metric(get_text('vip_discount_rate', lang), f"{discount_rate:.1f}%")
    
    st.markdown("---")
    
    # 快照匹配情况（活动后）
    if len(df_vip_after) > 0:
        st.subheader(get_text('vip_snapshot_match', lang))
        
        in_snapshot = len(df_vip_after[df_vip_after['In_Snapshot'] == True])
        not_in_snapshot = len(df_vip_after[df_vip_after['In_Snapshot'] == False])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 快照匹配饼图
            snapshot_data = pd.DataFrame({
                'Status': [get_text('vip_in_snapshot', lang), get_text('vip_not_in_snapshot', lang)],
                'Count': [in_snapshot, not_in_snapshot]
            })
            
            fig_snapshot = px.pie(
                snapshot_data,
                values='Count',
                names='Status',
                title=get_text('vip_snapshot_match', lang) if lang == 'zh' else 'Snapshot Match Status',
                color_discrete_sequence=['#10b981', '#94a3b8']
            )
            fig_snapshot.update_traces(textposition='inside', textinfo='percent+label')
            fig_snapshot.update_layout(
                margin=dict(l=20, r=20, t=50, b=20),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
            )
            st.plotly_chart(fig_snapshot, use_container_width=True)
        
        with col2:
            # 折扣享受情况
            st.subheader(get_text('vip_discount_status', lang))
            
            enjoyed = len(df_vip_after[df_vip_after['Status'] == '✅已享受'])
            not_enjoyed = len(df_vip_after[df_vip_after['Status'] == '❌未享受'])
            not_in_snap = len(df_vip_after[df_vip_after['Status'] == '❓不在快照'])
            
            discount_data = pd.DataFrame({
                'Status': [get_text('vip_enjoyed', lang), get_text('vip_not_enjoyed', lang), get_text('vip_not_in_snapshot', lang)],
                'Count': [enjoyed, not_enjoyed, not_in_snap]
            })
            
            fig_discount = px.bar(
                discount_data,
                x='Status',
                y='Count',
                title=get_text('vip_discount_status', lang) if lang == 'zh' else 'Discount Status',
                color='Status',
                color_discrete_map={
                    get_text('vip_enjoyed', lang): '#10b981',
                    get_text('vip_not_enjoyed', lang): '#ef4444',
                    get_text('vip_not_in_snapshot', lang): '#94a3b8'
                }
            )
            fig_discount.update_layout(
                margin=dict(l=20, r=20, t=50, b=40),
                showlegend=False,
                xaxis_title='',
                yaxis_title=get_text('count', lang) if lang == 'zh' else 'Count'
            )
            st.plotly_chart(fig_discount, use_container_width=True)
    
    st.markdown("---")
    
    # 各链特权用户购卡情况
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(get_text('vip_by_chain', lang))
        chain_stats = df_vip.groupby('Chain').agg({
            'Card_Value': 'count',
            'Actual_Paid': 'sum',
            'VIP_Discount': 'sum'
        }).reset_index()
        chain_stats.columns = ['Chain', 'Count', 'Revenue', 'Discount']
        
        fig_vip_chain = px.bar(
            chain_stats,
            x='Chain',
            y='Count',
            title=get_text('vip_by_chain', lang) if lang == 'zh' else 'VIP Purchases by Chain',
            color='Chain',
            color_discrete_map=get_chain_color_map(chain_stats['Chain'].unique()),
            text='Count'
        )
        fig_vip_chain.update_traces(textposition='outside')
        fig_vip_chain.update_layout(
            margin=dict(l=20, r=20, t=50, b=40),
            showlegend=False,
            xaxis_title='',
            yaxis_title=get_text('count', lang) if lang == 'zh' else 'Count'
        )
        st.plotly_chart(fig_vip_chain, use_container_width=True)
    
    with col2:
        st.subheader(get_text('vip_by_card_value', lang))
        value_stats = df_vip.groupby('Card_Value').size().reset_index(name='Count')
        value_stats['Card_Value'] = value_stats['Card_Value'].astype(str) + ' USD'
        
        fig_vip_value = px.pie(
            value_stats,
            values='Count',
            names='Card_Value',
            title=get_text('vip_by_card_value', lang) if lang == 'zh' else 'VIP Purchases by Card Value',
            color_discrete_sequence=px.colors.sequential.Teal
        )
        fig_vip_value.update_traces(textposition='inside', textinfo='percent+label')
        fig_vip_value.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
        )
        st.plotly_chart(fig_vip_value, use_container_width=True)
    
    # Insights Summary
    st.markdown("---")
    st.subheader(get_text('vip_insights', lang))
    
    # 计算关键指标
    if len(df_vip_after) > 0:
        in_snapshot_pct = in_snapshot / len(df_vip_after) * 100
        enjoyed_pct = enjoyed / len(df_vip_after) * 100
        
        if lang == 'zh':
            insights_md = f"""
            ### 📊 关键发现
            
            **活动效果优秀！** NFT持有者30%折扣活动自2025年7月21日启动以来：
            
            - ✅ **{enjoyed_pct:.1f}%** 的活动后交易成功享受了折扣
            - 📸 **{in_snapshot_pct:.1f}%** 的用户在有效快照期内购卡
            - 🎯 **{not_enjoyed}笔** 交易在快照期内但未享受折扣（需检查）
            - 📝 **{not_in_snap}笔** 交易不在快照期内（用户在非快照期购卡，属正常情况）
            
            ### 💡 业务洞察
            
            1. **系统运行状况**: {"完美！所有在快照期内的用户都享受了折扣" if not_enjoyed == 0 else f"需关注{not_enjoyed}笔未享受折扣的交易"}
            2. **快照机制有效性**: {in_snapshot_pct:.1f}%的用户在快照期内购卡，有效防止了套利行为
            3. **用户参与度**: {purchased_users}位NFT持有者参与购卡，占总特权用户的{purchased_users/total_vip_users*100:.1f}%
            4. **平均节省**: 每笔享受折扣的交易平均节省 ${df_vip_after[df_vip_after['Status']=='✅已享受']['Savings'].mean():.2f}
            
            {get_text('vip_activity_note', lang)}
            """
        else:
            insights_md = f"""
            ### 📊 Key Findings
            
            **Excellent Performance!** Since the NFT holder 30% discount activity started on July 21, 2025:
            
            - ✅ **{enjoyed_pct:.1f}%** of post-activity transactions successfully received discounts
            - 📸 **{in_snapshot_pct:.1f}%** of users purchased within valid snapshot periods
            - 🎯 **{not_enjoyed} transactions** were in snapshot period but didn't receive discount (needs review)
            - 📝 **{not_in_snap} transactions** were outside snapshot periods (users purchased outside snapshot window, normal behavior)
            
            ### 💡 Business Insights
            
            1. **System Status**: {"Perfect! All users in snapshot period received discounts" if not_enjoyed == 0 else f"Need to review {not_enjoyed} transactions without discount"}
            2. **Snapshot Mechanism Effectiveness**: {in_snapshot_pct:.1f}% of users purchased within snapshot periods, effectively preventing arbitrage
            3. **User Engagement**: {purchased_users} NFT holders participated, {purchased_users/total_vip_users*100:.1f}% of total VIP users
            4. **Average Savings**: ${df_vip_after[df_vip_after['Status']=='✅已享受']['Savings'].mean():.2f} saved per discounted transaction
            
            {get_text('vip_activity_note', lang)}
            """
        
        st.markdown(insights_md)
else:
    if lang == 'zh':
        st.info("💡 VIP用户分析数据尚未生成。请先运行 `python analyze_vip_users.py` 生成分析数据。")
    else:
        st.info("💡 VIP user analysis data not yet generated. Please run `python analyze_vip_users.py` first.")

st.markdown("---")

# 6. 原始交易数据
st.markdown('<div id="6"></div>', unsafe_allow_html=True)
st.header(get_text('raw_transaction_data', lang))

# 动态洞察摘要
if lang == 'zh':
    st.markdown(f"""
    **📊 数据摘要与洞察**  
    下方展示了所有链上交易的原始数据，包括交易哈希、时间戳、钱包地址、支付代币等详细信息。
    原始数据支持导出和审计，确保业务透明度和可追溯性，为客服、财务对账和合规审查提供可靠依据。
    """)
else:
    st.markdown(f"""
    **📊 Data Summary & Insights**  
    Raw on-chain transaction data is displayed below, including transaction hashes, timestamps, wallet addresses, payment tokens, and more.
    Raw data supports export and audit, ensuring business transparency and traceability for customer service, financial reconciliation, and compliance review.
    """)

st.markdown("")

# 格式化显示
df_display = df_filtered[['DateTime', 'Chain', 'Card_Value', 'Amount', 'Fee', 'Fee_Percentage', 'Asset', 'TxHash']].copy()
if lang == 'zh':
df_display.columns = ['时间', '链', '卡片面值(USD)', '实付金额(USD)', '手续费(USD)', '手续费率(%)', '支付代币', '交易哈希']
else:
    df_display.columns = ['DateTime', 'Chain', 'Card Value(USD)', 'Amount(USD)', 'Fee(USD)', 'Fee Rate(%)', 'Asset', 'TxHash']
df_display = df_display.sort_values(df_display.columns[0], ascending=False)

if lang == 'zh':
    format_dict = {
        '卡片面值(USD)': '{:.0f}',
        '实付金额(USD)': '{:.2f}',
        '手续费(USD)': '{:.2f}',
        '手续费率(%)': '{:.2f}'
    }
else:
    format_dict = {
        'Card Value(USD)': '{:.0f}',
        'Amount(USD)': '{:.2f}',
        'Fee(USD)': '{:.2f}',
        'Fee Rate(%)': '{:.2f}'
    }

st.dataframe(
    df_display.head(100).style.format(format_dict),
    use_container_width=True
)

# 下载按钮
csv = df_display.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label=get_text('download_data', lang),
    data=csv,
    file_name=f'gmt_pay_transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
    mime='text/csv',
)

# ===== 注销返还数据分析 =====
st.markdown("---")
st.markdown('<div id="refund"></div>', unsafe_allow_html=True)
st.markdown(f"## {get_text('refund_data', lang)}")
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
            border: 1px solid rgba(16, 185, 129, 0.3); 
            border-radius: 16px; 
            padding: 24px; 
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(16, 185, 129, 0.1);">
<p style="color: #1a1a1a; margin: 0; line-height: 1.8;">
<strong style="color: #059669;">{get_text('promo_title', lang)}</strong>: {get_text('promo_desc', lang)}<br>
<strong style="color: #059669;">{get_text('refund_addr_label', lang)}</strong>: <code style="background: rgba(16, 185, 129, 0.15); color: #1a1a1a; padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.3);">0x6f724c70500d899883954a5ac2e6f38d25422f60</code> <span style="color: #1a1a1a;">(Polygon)</span>
</p>
</div>
""", unsafe_allow_html=True)

# 加载注销返还数据
df_refund = load_refund_data()

# 动态洞察摘要
if not df_refund.empty:
    total_refunds = len(df_refund)
    total_refund_amount = df_refund['Amount'].sum()
    avg_refund = df_refund['Amount'].mean()
    
    if lang == 'zh':
        st.markdown(f"""
        **📊 数据摘要与洞察**  
        已处理 **{total_refunds}** 笔卡片注销返还，累计返还 **{total_refund_amount:,.2f} GGUSD**，平均每笔 **${avg_refund:.2f}**。
        GGUSD返还政策降低了用户注销卡片的心理负担，有效提升了用户体验和品牌忠诚度，同时促进了GGUSD代币的流通。
        """)
    else:
        st.markdown(f"""
        **📊 Data Summary & Insights**  
        Processed **{total_refunds}** card cancellations, total refund **{total_refund_amount:,.2f} GGUSD**, average **${avg_refund:.2f}** per refund.
        GGUSD refund policy reduces user friction for card cancellation, enhancing UX and brand loyalty while boosting GGUSD circulation.
        """)
    
    st.markdown("")

if not df_refund.empty:
    # 关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    total_refunds = len(df_refund)
    total_amount = df_refund['Amount'].sum()
    avg_refund = df_refund['Amount'].mean()
    
    # 估算原卡片余额 (返还额是余额的50%)
    estimated_card_balance = total_amount * 2
    
    with col1:
        st.metric(get_text('total_refunds', lang), f"{total_refunds:,}")
    
    with col2:
        st.metric(get_text('total_refund_amount', lang), f"${total_amount:,.2f}")
    
    with col3:
        st.metric(get_text('avg_refund', lang), f"${avg_refund:.2f}")
    
    with col4:
        st.metric("💳 " + ("估算注销卡片总余额" if lang == 'zh' else "Est. Card Balance"), f"${estimated_card_balance:,.2f}")
    
    # 时间趋势图
    st.markdown("### " + get_text('refund_trend', lang))
    df_refund_daily = df_refund.copy()
    df_refund_daily['Date'] = df_refund_daily['DateTime'].dt.date
    daily_stats = df_refund_daily.groupby('Date').agg({
        'Amount': ['sum', 'count']
    }).reset_index()
    daily_stats.columns = ['Date', 'Total_Amount', 'Count']
    
    fig_refund_trend = go.Figure()
    fig_refund_trend.add_trace(go.Bar(
        x=daily_stats['Date'],
        y=daily_stats['Total_Amount'],
        name='Refund Amount' if lang == 'en' else '返还金额',
        marker_color='#10b981',
        yaxis='y',
        hovertemplate=('Date: %{x}<br>Amount: $%{y:.2f}<extra></extra>' if lang == 'en' 
                      else '日期: %{x}<br>返还金额: $%{y:.2f}<extra></extra>')
    ))
    fig_refund_trend.add_trace(go.Scatter(
        x=daily_stats['Date'],
        y=daily_stats['Count'],
        name='Refund Count' if lang == 'en' else '返还笔数',
        marker_color='#f59e0b',
        yaxis='y2',
        mode='lines+markers',
        hovertemplate=('Date: %{x}<br>Count: %{y}<extra></extra>' if lang == 'en' 
                      else '日期: %{x}<br>返还笔数: %{y}<extra></extra>')
    ))
    fig_refund_trend.update_layout(
        title='Daily Refund Trend' if lang == 'en' else '每日注销返还趋势',
        xaxis_title='Date' if lang == 'en' else '日期',
        yaxis_title='Refund Amount (GGUSD)' if lang == 'en' else '返还金额 (GGUSD)',
        yaxis2=dict(
            title='Refund Count' if lang == 'en' else '返还笔数',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_refund_trend, use_container_width=True)
    
    # 返还金额分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### " + get_text('refund_distribution', lang))
        fig_refund_dist = px.histogram(
            df_refund,
            x='Amount',
            nbins=30,
            title='Refund Amount Distribution' if lang == 'en' else '返还金额分布直方图',
            labels={'Amount': 'Refund Amount (GGUSD)' if lang == 'en' else '返还金额 (GGUSD)', 
                    'count': 'Count' if lang == 'en' else '笔数'},
            color_discrete_sequence=['#8b5cf6']
        )
        fig_refund_dist.update_layout(height=350)
        st.plotly_chart(fig_refund_dist, use_container_width=True)
    
    with col2:
        st.markdown("### " + get_text('monthly_stats', lang))
        df_refund_monthly = df_refund.copy()
        df_refund_monthly['YearMonth'] = df_refund_monthly['DateTime'].dt.to_period('M').astype(str)
        monthly_stats = df_refund_monthly.groupby('YearMonth').agg({
            'Amount': ['sum', 'count']
        }).reset_index()
        monthly_stats.columns = ['YearMonth', 'Total_Amount', 'Count']
        
        fig_monthly = go.Figure(data=[
            go.Bar(
                x=monthly_stats['YearMonth'],
                y=monthly_stats['Total_Amount'],
                text=monthly_stats['Count'],
                texttemplate=('%{text} txs<br>$%{y:.0f}' if lang == 'en' else '%{text} 笔<br>$%{y:.0f}'),
                textposition='auto',
                marker_color='#06b6d4',
                hovertemplate=('Month: %{x}<br>Amount: $%{y:.2f}<br>Count: %{text}<extra></extra>' if lang == 'en' 
                              else '月份: %{x}<br>返还金额: $%{y:.2f}<br>笔数: %{text}<extra></extra>')
            )
        ])
        fig_monthly.update_layout(
            title='Monthly Refund Statistics' if lang == 'en' else '月度返还统计',
            xaxis_title='Month' if lang == 'en' else '月份',
            yaxis_title='Refund Amount (GGUSD)' if lang == 'en' else '返还金额 (GGUSD)',
            height=350
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    # 详细数据表
    with st.expander("📋 " + (get_text('refund_details', lang) if lang == 'zh' else get_text('refund_details', lang)), expanded=False):
        df_refund_display = df_refund[['DateTime', 'Amount', 'To', 'TxHash']].copy()
        df_refund_display['DateTime'] = df_refund_display['DateTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_refund_display['Amount'] = df_refund_display['Amount'].apply(lambda x: f"${x:.2f}")
        if lang == 'zh':
        df_refund_display.columns = ['时间', '返还金额 (GGUSD)', '接收地址', '交易哈希']
        else:
            df_refund_display.columns = ['DateTime', 'Refund Amount (GGUSD)', 'To Address', 'TxHash']
        
        st.dataframe(
            df_refund_display.sort_values(df_refund_display.columns[0], ascending=False),
            use_container_width=True,
            height=400
        )
        
        # 下载按钮
        csv_refund = df_refund_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label=get_text('download_refund_data', lang),
            data=csv_refund,
            file_name=f'gmt_pay_refunds_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
        )
else:
    st.info(get_text('no_refund_data', lang))

# 页脚
st.markdown("---")
footer_title = "💳 GMT Pay Data Dashboard" if lang == 'en' else "💳 GMT Pay 数据看板"
footer_chains_label = "🔗 Supported Chains:" if lang == 'en' else "🔗 支持链:"
footer_tokens_label = "💰 Supported Tokens:" if lang == 'en' else "💰 支持代币:"
footer_realtime = "⚡ Real-time blockchain data" if lang == 'en' else "⚡ 数据实时从区块链抓取"
footer_cache = "🔄 Auto-cache 30 min" if lang == 'en' else "🔄 自动缓存30分钟"

st.markdown(f"""
<div style='text-align: center; 
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.05) 100%);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 16px;
            padding: 30px;
            margin-top: 40px;'>
    <p style='color: #1a1a1a; font-size: 24px; font-weight: 800; margin-bottom: 15px;'>
    {footer_title}</p>
    <p style='color: #1a1a1a; font-size: 16px; line-height: 1.8;'>
    {footer_chains_label} <span style="color: #1a1a1a;">Ethereum · BNB Chain · Polygon · Solana</span><br>
    {footer_tokens_label} <span style="color: #1a1a1a;">GGUSD · USDT · USDC · BUSD</span></p>
    <p style='margin-top: 20px;'>
    🌐 <a href="https://fsl.com/gmtpay" target="_blank" style="color: #10b981; text-decoration: none; font-weight: 700;">fsl.com/gmtpay</a></p>
    <p style='color: #1a1a1a; font-size: 14px; margin-top: 20px; opacity: 0.8;'>
    {footer_realtime} | {footer_cache}</p>
</div>
""", unsafe_allow_html=True)

