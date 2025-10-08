"""
GMT Pay 链上数据抓取模块
支持从 EVM 链和 Solana 链实时抓取交易数据
"""

import sys
import io

# 简单的日志函数，避免I/O错误（在Streamlit环境中print可能失败）
def log_message(msg):
    """安全的日志输出"""
    pass  # 在生产环境中静默，避免I/O错误

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import streamlit as st

# 加载环境变量（优先使用Streamlit Secrets，其次是.env文件）
load_dotenv()

def get_api_key(key_name):
    """获取API Key，优先从Streamlit Secrets读取"""
    try:
        # 尝试从Streamlit Secrets读取（部署环境）
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except:
        pass
    # 回退到环境变量（本地开发）
    return os.getenv(key_name)


class ChainDataFetcher:
    """链上数据抓取器基类"""
    
    def __init__(self):
        self.data_cache = {}
        self.cache_timestamp = {}
        self.cache_duration = 300  # 缓存5分钟
    
    def fetch_transactions(self, address: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """抓取交易数据（需在子类中实现）"""
        raise NotImplementedError


class EtherscanFetcher(ChainDataFetcher):
    """
    Etherscan API 数据抓取器
    支持 Ethereum, BSC, Polygon 等 EVM 链
    """
    
    # API 端点配置 (使用 Etherscan V2 统一 API)
    API_ENDPOINTS = {
        'ethereum': {
            'url': 'https://api.etherscan.io/v2/api',
            'chainid': 1,  # Ethereum Mainnet
            'env_key': 'ETHERSCAN_API_KEY',
            'chain_name': 'Ethereum'
        },
        'bsc': {
            'url': 'https://api.etherscan.io/v2/api',
            'chainid': 56,  # BNB Smart Chain
            'env_key': 'ETHERSCAN_API_KEY',  # V2 API使用统一Key
            'chain_name': 'BNB Chain'
        },
        'polygon': {
            'url': 'https://api.etherscan.io/v2/api',
            'chainid': 137,  # Polygon Mainnet
            'env_key': 'ETHERSCAN_API_KEY',  # V2 API使用统一Key
            'chain_name': 'Polygon'
        }
    }
    
    def __init__(self, chain: str = 'bsc'):
        super().__init__()
        self.chain = chain
        self.config = self.API_ENDPOINTS.get(chain)
        if not self.config:
            raise ValueError(f"不支持的链: {chain}")
        
        # 获取 API Key
        self.api_key = os.getenv(self.config['env_key'], '')
        if not self.api_key:
            safe_log_message(f"警告: 未设置 {self.config['env_key']}, 将使用免费API限制")
    
    def fetch_token_transfers(self, address: str, start_timestamp: int = None, 
                             end_timestamp: int = None, page: int = 1, 
                             offset: int = 100) -> List[Dict]:
        """
        抓取代币转账记录（使用 Etherscan API V2）
        
        Args:
            address: 收款地址
            start_timestamp: 开始时间戳
            end_timestamp: 结束时间戳
            page: 页码
            offset: 每页数量
        
        Returns:
            交易列表
        """
        # 使用 V2 API 端点
        # 例如: https://api.etherscan.io/api -> https://api.etherscan.io/v2/api
        base_url = self.config['url']
        if base_url.endswith('/api'):
            v2_url = base_url[:-4] + '/v2/api'
        else:
            v2_url = base_url + '/v2'
        
        params = {
            'chainid': self.config['chainid'],
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'page': page,
            'offset': offset,
            'sort': 'desc',
            'apikey': self.api_key
        }
        
        if start_timestamp:
            params['startblock'] = 0
        if end_timestamp:
            params['endblock'] = 99999999
        
        try:
            # 使用 Etherscan V2 API (支持统一chainid参数)
            response = requests.get(self.config['url'], params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # 确保data是字典类型
            if not isinstance(data, dict):
                log_message(f"  {self.config['chain_name']} API返回格式错误: {type(data)}")
                return []
            
            if data.get('status') == '1' and data.get('result'):
                result = data['result']
                # result可能是字符串(错误信息)或列表(交易数据)
                if isinstance(result, list):
                    return result
                else:
                    log_message(f"  {self.config['chain_name']} API返回: {result}")
                    return []
            else:
                error_msg = data.get('message', '')
                # 忽略 deprecated 警告，继续返回结果
                if error_msg and 'deprecated' not in error_msg.lower() and error_msg != 'NOTOK':
                    log_message(f"  {self.config['chain_name']} API 返回: {error_msg}")
                return []
        
        except requests.exceptions.RequestException as e:
            safe_log_message(f"  {self.config['chain_name']} 请求失败: {e}")
            return []
        except Exception as e:
            safe_log_message(f"  {self.config['chain_name']} 处理数据时出错: {e}")
            return []
    
    def fetch_transactions(self, address: str, days: int = 100, direction: str = 'inflow') -> pd.DataFrame:
        """
        抓取最近 N 天的交易数据
        
        Args:
            address: 钱包地址
            days: 天数
            direction: 'inflow' (转入) 或 'outflow' (转出)
        
        Returns:
            DataFrame 格式的交易数据
        """
        log_message(f"正在抓取 {self.config['chain_name']} 链的数据 ({'转出' if direction == 'outflow' else '转入'})...")
        
        all_transactions = []
        page = 1
        max_pages = 100  # 增加最大页数以获取更多历史数据
        cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        
        while page <= max_pages:
            transactions = self.fetch_token_transfers(address, page=page, offset=100)
            
            if not transactions:
                break
            
            # 检查是否已经超出时间范围
            oldest_tx_time = min(int(tx.get('timeStamp', 0)) for tx in transactions)
            if oldest_tx_time < cutoff_timestamp:
                # 只添加在时间范围内的交易
                transactions = [tx for tx in transactions if int(tx.get('timeStamp', 0)) >= cutoff_timestamp]
                all_transactions.extend(transactions)
                log_message(f"  已获取 {len(all_transactions)} 条交易记录（已到达目标时间）")
                break
            
            all_transactions.extend(transactions)
            log_message(f"  已获取 {len(all_transactions)} 条交易记录...")
            
            # 如果获取的交易少于100条，说明已经是最后一页
            if len(transactions) < 100:
                break
            
            page += 1
            time.sleep(0.2)  # 避免API限流
        
        if not all_transactions:
            log_message(f"  {self.config['chain_name']}: 未找到交易记录")
            return pd.DataFrame()
        
        # 转换为 DataFrame
        df = pd.DataFrame(all_transactions)
        
        if df.empty:
            log_message(f"  {self.config['chain_name']}: 未找到交易记录")
            return pd.DataFrame()
        
        # 过滤最近 N 天的数据
        cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        df['timeStamp'] = df['timeStamp'].astype(int)
        df = df[df['timeStamp'] >= cutoff_timestamp]
        
        # 根据方向过滤
        if direction == 'inflow':
            # 只保留转入交易（to = address）
            df = df[df['to'].str.lower() == address.lower()]
        else:  # outflow
            # 只保留转出交易（from = address）
            df = df[df['from'].str.lower() == address.lower()]
        
        if df.empty:
            log_message(f"  {self.config['chain_name']}: 最近{days}天无交易记录")
            return pd.DataFrame()
        
        # 标准化数据格式
        df_processed = self._process_data(df, direction)
        
        log_message(f"  {self.config['chain_name']}: 成功获取 {len(df_processed)} 条有效交易")
        return df_processed
    
    def _process_data(self, df: pd.DataFrame, direction: str = 'inflow') -> pd.DataFrame:
        """处理和标准化数据"""
        result = pd.DataFrame()
        
        # 时间转换
        result['DateTime'] = pd.to_datetime(df['timeStamp'].astype(int), unit='s')
        
        # 金额转换 (考虑代币精度)
        result['Amount'] = df.apply(lambda row: 
            float(row['value']) / (10 ** int(row['tokenDecimal'])) 
            if row['tokenDecimal'] else 0, axis=1
        )
        
        # 代币识别
        result['Asset'] = df.apply(lambda row: self._identify_token(
            row.get('tokenSymbol', ''),
            row.get('contractAddress', '')
        ), axis=1)
        
        # 链信息
        result['Chain'] = self.config['chain_name']
        
        # 交易哈希和地址
        result['TxHash'] = df['hash']
        result['From'] = df['from']
        result['To'] = df['to']
        
        # 方向标记
        result['Direction'] = direction
        
        # 过滤无效金额
        result = result[result['Amount'] > 0]
        
        return result
    
    def _identify_token(self, symbol: str, contract_address: str) -> str:
        """识别代币类型"""
        symbol_upper = symbol.upper()
        contract_lower = contract_address.lower()
        
        # 代币合约地址 (统一小写)
        GGUSD_CONTRACT = '0xffffff9936bd58a008855b0812b44d2c8dffe2aa'
        BUSD_CONTRACT = '0x55d398326f99059ff775485246999027b3197955'  # BSC-USD (BUSD)
        
        # 优先使用合约地址识别
        if contract_lower == GGUSD_CONTRACT:
            return 'GGUSD'
        elif contract_lower == BUSD_CONTRACT:
            return 'BUSD'
        # 然后使用symbol识别
        elif 'GGUSD' in symbol_upper:
            return 'GGUSD'
        elif 'BUSD' in symbol_upper or 'BSC-USD' in symbol_upper:
            return 'BUSD'
        elif 'USDT' in symbol_upper:
            return 'USDT'
        elif 'USDC' in symbol_upper:
            return 'USDC'
        else:
            return 'Other'


class SolanaFetcher(ChainDataFetcher):
    """
    Solana 链数据抓取器
    使用 Solana RPC API 和 Helius API
    """
    
    def __init__(self):
        super().__init__()
        self.chain_name = 'Solana'
        
        # 优先使用 Helius Enhanced API
        self.helius_api_key = os.getenv('HELIUS_API_KEY', '')
        
        if self.helius_api_key:
            log_message("使用 Helius Enhanced API")
            self.helius_api_url = f'https://api.helius.xyz/v0/addresses'
        else:
            log_message("警告: 未设置 HELIUS_API_KEY, Solana 数据获取可能失败")
            self.helius_api_url = None
    
    def fetch_transactions(self, address: str, days: int = 100) -> pd.DataFrame:
        """
        抓取 Solana 地址的交易记录
        
        Args:
            address: Solana 地址
            days: 天数
        
        Returns:
            DataFrame 格式的交易数据
        """
        log_message(f"正在抓取 Solana 链的数据...")
        
        if self.helius_api_key:
            # 使用组合方式: RPC 获取所有签名 + Enhanced API 解析
            return self._fetch_with_helius_enhanced(address, days)
        else:
            log_message("  错误: 未配置 Helius API Key")
            return pd.DataFrame()
    
    def _fetch_with_helius_enhanced(self, address: str, days: int) -> pd.DataFrame:
        """
        使用 Helius RPC + Enhanced API 抓取交易历史
        
        Solana 特殊处理: SPL token 转账发生在 Token Accounts 上,不是主地址
        步骤:
        1. 获取主地址的所有 Token Accounts
        2. 获取每个 Token Account 的交易签名
        3. 使用 Enhanced API 批量解析交易详情
        """
        log_message("  使用 Helius RPC + Enhanced API...")
        
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        rpc_url = f'https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}'
        
        try:
            # 步骤1: 获取所有 Token Accounts
            log_message("  步骤1: 获取 Token Accounts...")
            token_accounts_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    address,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"}
                ]
            }
            
            response = requests.post(rpc_url, json=token_accounts_payload, timeout=30)
            result = response.json()
            
            if 'error' in result:
                log_message(f"  获取 Token Accounts 失败: {result['error']}")
                return pd.DataFrame()
            
            token_accounts = result.get('result', {}).get('value', [])
            log_message(f"  找到 {len(token_accounts)} 个 Token Accounts")
            
            # 步骤2: 获取每个 Token Account 的交易签名
            log_message("  步骤2: 获取交易签名列表...")
            all_signatures = []
            
            for acc in token_accounts:
                token_account_address = acc['pubkey']
                mint = acc['account']['data']['parsed']['info'].get('mint', '')
                
                # 只处理我们关心的代币
                USDC_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
                GGUSD_MINT = 'GGUSDyBUPFg5RrgWwqEqhXoha85iYGs6cL57SyK4G2Y7'
                USDT_MINT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
                
                if mint not in [USDC_MINT, GGUSD_MINT, USDT_MINT]:
                    continue
                
                token_name = 'USDC' if mint == USDC_MINT else ('GGUSD' if mint == GGUSD_MINT else 'USDT')
                
                # 获取该 Token Account 的所有交易签名
                before_signature = None
                for iteration in range(20):
                    rpc_payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getSignaturesForAddress",
                        "params": [token_account_address, {"limit": 1000}]
                    }
                    
                    if before_signature:
                        rpc_payload["params"][1]["before"] = before_signature
                    
                    response = requests.post(rpc_url, json=rpc_payload, timeout=30)
                    result = response.json()
                    
                    if 'error' in result:
                        break
                    
                    signatures = result.get('result', [])
                    if not signatures:
                        break
                    
                    # 过滤时间范围内的签名
                    valid_signatures = []
                    for sig in signatures:
                        block_time = sig.get('blockTime', 0)
                        if block_time >= cutoff_timestamp:
                            valid_signatures.append(sig['signature'])
                        else:
                            break
                    
                    all_signatures.extend(valid_signatures)
                    
                    if len(valid_signatures) < len(signatures) or len(signatures) < 1000:
                        break
                    
                    before_signature = signatures[-1]['signature']
                    time.sleep(0.1)
                
                log_message(f"    {token_name}: {len([s for s in all_signatures if s not in [sig for sig in all_signatures[:len(all_signatures)-len(valid_signatures)]]])} 个签名")
            
            # 去重
            all_signatures = list(set(all_signatures))
            log_message(f"  总计(去重后): {len(all_signatures)} 个交易签名")
            
            if not all_signatures:
                log_message(f"  Solana: 最近{days}天无交易记录")
                return pd.DataFrame()
            
            # 步骤3: 批量解析交易 (使用 Enhanced API)
            log_message("  步骤3: 解析交易详情...")
            all_token_transfers = []
            
            # Helius parseTransactions API 一次最多100个交易
            batch_size = 100
            parse_url = 'https://api.helius.xyz/v0/transactions'
            
            for i in range(0, len(all_signatures), batch_size):
                batch = all_signatures[i:i+batch_size]
                
                params = {'api-key': self.helius_api_key}
                payload = {"transactions": batch}
                
                response = requests.post(parse_url, params=params, json=payload, timeout=30)
                response.raise_for_status()
                
                transactions = response.json()
                
                # 解析每个交易的 token transfers
                for tx in transactions:
                    tx_timestamp = tx.get('timestamp', 0)
                    token_transfers = tx.get('tokenTransfers', [])
                    
                    for transfer in token_transfers:
                        # 只保留转入到目标地址的交易
                        if transfer.get('toUserAccount', '').lower() == address.lower():
                            all_token_transfers.append({
                                'timestamp': tx_timestamp,
                                'signature': tx.get('signature', ''),
                                'mint': transfer.get('mint', ''),
                                'tokenAmount': transfer.get('tokenAmount', 0),
                                'fromUserAccount': transfer.get('fromUserAccount', ''),
                            })
                
                if (i + batch_size) % 500 == 0 or i + batch_size >= len(all_signatures):
                    log_message(f"    已解析 {min(i+batch_size, len(all_signatures))}/{len(all_signatures)}, 找到 {len(all_token_transfers)} 个 token transfers")
                time.sleep(0.2)
            
            if not all_token_transfers:
                log_message(f"  Solana: 最近{days}天无 token 转账记录")
                return pd.DataFrame()
            
            # 转换为 DataFrame
            df = pd.DataFrame(all_token_transfers)
            
            # 标准化数据格式
            result = pd.DataFrame()
            result['DateTime'] = pd.to_datetime(df['timestamp'], unit='s')
            result['Amount'] = df['tokenAmount'].astype(float)
            result['Chain'] = 'Solana'
            result['TxHash'] = df['signature']
            result['From'] = df['fromUserAccount']
            
            # 识别代币类型
            USDC_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
            GGUSD_MINT = 'GGUSDyBUPFg5RrgWwqEqhXoha85iYGs6cL57SyK4G2Y7'
            
            result['Asset'] = df['mint'].apply(lambda x: 
                'USDC' if x == USDC_MINT 
                else ('GGUSD' if x == GGUSD_MINT else 'Other'))
            
            # 过滤有效数据
            result = result.dropna(subset=['Amount', 'DateTime'])
            result = result[result['Amount'] > 0]
            
            log_message(f"  Solana: 成功获取 {len(result)} 条有效交易")
            return result
            
        except requests.exceptions.RequestException as e:
            log_message(f"  Helius API 请求失败: {e}")
            return pd.DataFrame()
        except Exception as e:
            log_message(f"  处理 Solana 数据时出错: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _fetch_from_excel(self, excel_file: str, days: int) -> pd.DataFrame:
        """从 Excel 文件读取 Solana 数据"""
        log_message(f"  从 Excel 文件读取: {excel_file}")
        
        try:
            df = pd.read_excel(excel_file)
            
            # 转换时间列
            df['DateTime'] = pd.to_datetime(df['Human Time'], errors='coerce')
            
            # 移除时区信息以便比较
            if df['DateTime'].dt.tz is not None:
                df['DateTime'] = df['DateTime'].dt.tz_localize(None)
            
            # 过滤时间范围
            cutoff_time = datetime.now() - timedelta(days=days)
            df = df[df['DateTime'] >= cutoff_time]
            
            # 标准化数据格式
            result = pd.DataFrame()
            result['DateTime'] = df['DateTime']
            result['Amount'] = df['Value']
            result['Chain'] = 'Solana'
            result['TxHash'] = df['Signature']
            result['From'] = df['From']
            
            # 识别代币类型
            USDC_ADDRESS = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
            GGUSD_ADDRESS = 'GGUSDyBUPFg5RrgWwqEqhXoha85iYGs6cL57SyK4G2Y7'
            
            result['Asset'] = df['Token Address'].apply(lambda x: 
                'USDC' if USDC_ADDRESS in str(x) 
                else ('GGUSD' if GGUSD_ADDRESS in str(x)
                else 'Other'))
            
            # 过滤有效数据
            result = result.dropna(subset=['Amount', 'DateTime'])
            result = result[result['Amount'] > 0]
            
            log_message(f"  Solana: 从 Excel 读取 {len(result)} 条有效交易")
            return result
            
        except Exception as e:
            log_message(f"读取 Excel 文件错误: {e}")
            return pd.DataFrame()
    
    def _fetch_with_solscan(self, address: str, days: int) -> pd.DataFrame:
        """使用 Solscan API 抓取数据"""
        log_message("  使用 Solscan API...")
        
        # 使用公共 API v1.0
        base_url = "https://public-api.solscan.io"
        headers = {}  # 公共 API 不需要 token
        
        all_transactions = []
        page = 1
        page_size = 50
        max_pages = 100
        
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        try:
            while page <= max_pages:
                # 获取 SPL token transfers (使用 v1 API)
                url = f"{base_url}/account/token/txs"
                params = {
                    "account": address,
                    "offset": (page - 1) * page_size,
                    "limit": page_size
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                transactions = response.json()
                
                # v1 API 直接返回数组
                if not transactions or not isinstance(transactions, list):
                    break
                
                # 检查时间范围
                has_old_tx = False
                for tx in transactions:
                    tx_time = tx.get('blockTime', 0)
                    if tx_time < cutoff_timestamp:
                        has_old_tx = True
                        break
                    # 只保留转入交易 (dst 是目标地址)
                    if tx.get('dst') == address:
                        all_transactions.append(tx)
                
                log_message(f"  Solscan: 已获取 {len(all_transactions)} 条交易...")
                
                if has_old_tx or len(transactions) < page_size:
                    break
                
                page += 1
                time.sleep(0.5)  # API 限流
            
            if not all_transactions:
                log_message(f"  Solana: 未找到交易记录")
                return pd.DataFrame()
            
            return self._process_solscan_data(all_transactions, address)
        
        except Exception as e:
            log_message(f"Solscan API 错误: {e}")
            return pd.DataFrame()
    
    def _process_solscan_data(self, transactions: List[Dict], address: str) -> pd.DataFrame:
        """处理 Solscan API v1 返回的数据"""
        processed = []
        
        USDC_ADDRESS = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
        GGUSD_ADDRESS = 'GGUSDyBUPFg5RrgWwqEqhXoha85iYGs6cL57SyK4G2Y7'
        
        for tx in transactions:
            try:
                block_time = tx.get('blockTime')
                if not block_time:
                    continue
                
                # v1 API 中金额已经是正常值
                amount = float(tx.get('amount', 0))
                
                if amount <= 0:
                    continue
                
                # v1 API 中的代币信息
                token_address = tx.get('tokenAddress', '')
                if token_address == USDC_ADDRESS:
                    asset = 'USDC'
                elif token_address == GGUSD_ADDRESS:
                    asset = 'GGUSD'
                else:
                    asset = 'Other'
                
                processed.append({
                    'DateTime': datetime.fromtimestamp(block_time),
                    'Amount': amount,
                    'Asset': asset,
                    'Chain': 'Solana',
                    'TxHash': tx.get('txHash', ''),
                    'From': tx.get('src', 'Unknown')
                })
            except Exception as e:
                continue
        
        if not processed:
            return pd.DataFrame()
        
        df = pd.DataFrame(processed)
        df = df[df['Amount'] > 0]
        
        log_message(f"  Solana: 成功获取 {len(df)} 条有效交易")
        return df
    
    def _fetch_with_helius(self, address: str, days: int) -> pd.DataFrame:
        """使用 Helius Enhanced API 抓取数据"""
        url = f"https://api.helius.xyz/v0/addresses/{address}/transactions"
        params = {
            'api-key': self.helius_api_key,
            'limit': 100
        }
        
        all_transactions = []
        before_signature = None
        
        # 计算截止时间
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for _ in range(10):  # 最多获取10页
            if before_signature:
                params['before'] = before_signature
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                transactions = response.json()
                
                if not transactions:
                    break
                
                for tx in transactions:
                    tx_time = datetime.fromtimestamp(tx.get('timestamp', 0))
                    if tx_time < cutoff_time:
                        break
                    all_transactions.append(tx)
                
                # 如果最后一笔交易时间早于截止时间，停止获取
                last_tx_time = datetime.fromtimestamp(transactions[-1].get('timestamp', 0))
                if last_tx_time < cutoff_time:
                    break
                
                before_signature = transactions[-1].get('signature')
                time.sleep(0.2)
            
            except requests.exceptions.RequestException as e:
                log_message(f"Helius API 请求失败: {e}")
                break
        
        if not all_transactions:
            log_message(f"  Solana: 未找到交易记录")
            return pd.DataFrame()
        
        return self._process_solana_data(all_transactions, address)
    
    def _fetch_with_rpc(self, address: str, days: int) -> pd.DataFrame:
        """使用标准 RPC 抓取数据（支持分页）"""
        log_message("  使用标准 RPC 方法...")
        
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        all_transactions = []
        before_signature = None
        max_iterations = 50  # 最多迭代50次（每次1000个签名 = 最多50000个签名）
        
        for iteration in range(max_iterations):
            # 获取签名列表（每次最多1000个）
            params = [address, {"limit": 1000}]
            if before_signature:
                params[1]["before"] = before_signature
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": params
            }
            
            try:
                response = requests.post(self.rpc_url, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                signatures = data.get('result', [])
                
                if not signatures:
                    break
                
                # 检查最旧的交易时间
                oldest_sig_time = signatures[-1].get('blockTime', 0)
                if oldest_sig_time and oldest_sig_time < cutoff_timestamp:
                    # 只处理在时间范围内的签名
                    signatures = [sig for sig in signatures if sig.get('blockTime', 0) >= cutoff_timestamp]
                    if signatures:
                        # 获取这批交易的详细信息
                        for sig_info in signatures:
                            tx_detail = self._get_transaction_detail(sig_info.get('signature'))
                            if tx_detail:
                                all_transactions.append(tx_detail)
                        log_message(f"  Solana: 已获取 {len(all_transactions)} 条交易（已到达目标时间）")
                    break
                
                # 获取这批交易的详细信息
                for sig_info in signatures:
                    tx_detail = self._get_transaction_detail(sig_info.get('signature'))
                    if tx_detail:
                        all_transactions.append(tx_detail)
                    time.sleep(0.05)  # 减少延迟
                
                log_message(f"  Solana: 已获取 {len(all_transactions)} 条交易...")
                
                # 设置下一次迭代的起始点
                before_signature = signatures[-1].get('signature')
                
                # 如果返回的签名少于1000，说明已经到底了
                if len(signatures) < 1000:
                    break
                
                time.sleep(0.2)  # 避免限流
                
            except requests.exceptions.RequestException as e:
                log_message(f"Solana RPC 请求失败: {e}")
                break
        
        if not all_transactions:
            log_message(f"  Solana: 未找到有效交易")
            return pd.DataFrame()
        
        return self._process_solana_transactions(all_transactions, address)
    
    def _get_transaction_detail(self, signature: str) -> Optional[Dict]:
        """获取交易详情"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
            ]
        }
        
        try:
            response = requests.post(self.rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('result')
        except:
            return None
    
    def _process_solana_transactions(self, transactions: List[Dict], address: str) -> pd.DataFrame:
        """处理 Solana 交易数据"""
        processed = []
        
        # USDC 和 GGUSD 的代币地址
        USDC_ADDRESS = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
        GGUSD_ADDRESS = 'GGUSDyBUPFg5RrgWwqEqhXoha85iYGs6cL57SyK4G2Y7'
        
        for tx in transactions:
            if not tx:
                continue
            
            try:
                block_time = tx.get('blockTime')
                if not block_time:
                    continue
                
                meta = tx.get('meta', {})
                transaction = tx.get('transaction', {})
                message = transaction.get('message', {})
                
                # 解析代币转账
                post_balances = meta.get('postTokenBalances', [])
                pre_balances = meta.get('preTokenBalances', [])
                
                for post in post_balances:
                    mint = post.get('mint')
                    account_index = post.get('accountIndex')
                    
                    # 查找对应的 pre balance
                    pre = next((p for p in pre_balances if p.get('accountIndex') == account_index), None)
                    
                    if pre:
                        post_amount = float(post.get('uiTokenAmount', {}).get('uiAmount', 0))
                        pre_amount = float(pre.get('uiTokenAmount', {}).get('uiAmount', 0))
                        
                        amount = post_amount - pre_amount
                        
                        # 只保留转入交易
                        if amount > 0:
                            asset = 'USDC' if mint == USDC_ADDRESS else ('GGUSD' if mint == GGUSD_ADDRESS else 'Other')
                            
                            processed.append({
                                'DateTime': datetime.fromtimestamp(block_time),
                                'Amount': amount,
                                'Asset': asset,
                                'Chain': 'Solana',
                                'TxHash': tx.get('transaction', {}).get('signatures', [''])[0],
                                'From': 'Unknown'  # Solana 的发送者需要更复杂的解析
                            })
            except Exception as e:
                continue
        
        if not processed:
            return pd.DataFrame()
        
        df = pd.DataFrame(processed)
        df = df[df['Amount'] > 0]
        
        log_message(f"  Solana: 成功获取 {len(df)} 条有效交易")
        return df
    
    def _process_solana_data(self, transactions: List[Dict], address: str) -> pd.DataFrame:
        """处理 Helius API 返回的数据"""
        # 这里需要根据 Helius API 的实际返回格式进行处理
        # 简化版本
        return self._process_solana_transactions(transactions, address)


class GMTPayDataFetcher:
    """GMT Pay 数据抓取主类"""
    
    # GMT Pay 收款地址
    EVM_ADDRESS = '0x523ffC4D9782dC8af35664625fBB3e1d8e8ec6cb'
    SOLANA_ADDRESS = 'G7bMBQegH3RyRjt1QZu3o6BA2ZQQ7shdJ7zGrw7PwNEL'
    
    def __init__(self):
        self.fetchers = {
            'ethereum': EtherscanFetcher('ethereum'),
            'bsc': EtherscanFetcher('bsc'),
            'polygon': EtherscanFetcher('polygon'),
            'solana': SolanaFetcher()
        }
    
    def fetch_all_chains(self, days: int = 100) -> pd.DataFrame:
        """
        抓取所有链的数据
        
        Args:
            days: 抓取最近多少天的数据
        
        Returns:
            合并后的 DataFrame
        """
        all_data = []
        
        # 抓取 EVM 链数据
        for chain_name in ['ethereum', 'bsc', 'polygon']:
            try:
                fetcher = self.fetchers[chain_name]
                df = fetcher.fetch_transactions(self.EVM_ADDRESS, days=days)
                if not df.empty:
                    all_data.append(df)
            except Exception as e:
                log_message(f"抓取 {chain_name} 数据失败: {e}")
        
        # 抓取 Solana 链数据
        try:
            solana_fetcher = self.fetchers['solana']
            df_solana = solana_fetcher.fetch_transactions(self.SOLANA_ADDRESS, days=days)
            if not df_solana.empty:
                all_data.append(df_solana)
        except Exception as e:
            log_message(f"抓取 Solana 数据失败: {e}")
        
        # 合并所有数据
        if not all_data:
            log_message("\n警告: 所有链都未能获取到数据")
            return pd.DataFrame()
        
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values('DateTime', ascending=False)
        
        log_message(f"\n成功! 总计获取 {len(combined_df)} 条交易记录")
        return combined_df
    
    def save_to_cache(self, df: pd.DataFrame, cache_file: str = 'chain_data_cache.csv'):
        """保存数据到缓存文件"""
        try:
            df.to_csv(cache_file, index=False, encoding='utf-8-sig')
            log_message(f"数据已保存到缓存: {cache_file}")
        except Exception as e:
            log_message(f"保存缓存失败: {e}")
    
    def load_from_cache(self, cache_file: str = 'chain_data_cache.csv', 
                       max_age_minutes: int = 30) -> Optional[pd.DataFrame]:
        """
        从缓存加载数据
        
        Args:
            cache_file: 缓存文件路径
            max_age_minutes: 缓存有效期（分钟）
        
        Returns:
            DataFrame 或 None
        """
        if not os.path.exists(cache_file):
            return None
        
        # 检查缓存文件年龄
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > max_age_minutes * 60:
            log_message(f"缓存已过期 (超过 {max_age_minutes} 分钟)")
            return None
        
        try:
            df = pd.read_csv(cache_file, encoding='utf-8-sig')
            df['DateTime'] = pd.to_datetime(df['DateTime'])
            log_message(f"从缓存加载了 {len(df)} 条记录 (缓存年龄: {file_age/60:.1f} 分钟)")
            return df
        except Exception as e:
            log_message(f"加载缓存失败: {e}")
            return None


def main():
    """测试函数"""
    log_message("=" * 80)
    log_message("GMT Pay 链上数据抓取器")
    log_message("=" * 80)
    
    fetcher = GMTPayDataFetcher()
    
    # 尝试从缓存加载
    df = fetcher.load_from_cache(max_age_minutes=30)
    
    if df is None:
        # 缓存不存在或已过期，从链上抓取
        log_message("\n开始从链上抓取数据...\n")
        df = fetcher.fetch_all_chains(days=100)
        
        if not df.empty:
            # 保存到缓存
            fetcher.save_to_cache(df)
            
            # 显示统计信息
            log_message("\n" + "=" * 80)
            log_message("数据统计")
            log_message("=" * 80)
            log_message(f"总交易数: {len(df)}")
            log_message(f"日期范围: {df['DateTime'].min()} 到 {df['DateTime'].max()}")
            log_message(f"\n各链交易数:")
            log_message(df['Chain'].value_counts())
            log_message(f"\n各代币交易数:")
            log_message(df['Asset'].value_counts())
            log_message(f"\n总金额: ${df['Amount'].sum():,.2f}")
    
    return df


if __name__ == "__main__":
    df = main()
    if not df.empty:
        log_message("\n前10条记录:")
        log_message(df.head(10))

