# 💳 GMT Pay Dashboard

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Overview
Real-time monitoring and analytics dashboard for GMT Pay card sales, supporting multi-chain and multi-token data aggregation.

### ✨ Features

**Data Analytics**
- **Multi-Chain Support**: Ethereum, BNB Chain, Polygon, Solana
- **Multi-Token**: USDC, USDT (all chains), GGUSD (BNB/Polygon), BUSD (BNB)
- **Real-time Data**: Automatic on-chain transaction fetching
- **Visualizations**: Sales trends, chain distribution, time series analysis
- **User Analytics**: Holder behavior tracking and statistics

**Other Features**
- **Bilingual**: English/Chinese interface switching
- **Auto-Refresh**: Data updates every 30 minutes
- **Interactive**: Time range filtering, data export

### 🚀 Quick Start

**Requirements**
- Python 3.9+
- Blockchain API Keys

**Installation**
```bash
pip install -r requirements.txt
```

**Configuration**
Create `.env` file with your API keys:
```bash
ETHERSCAN_API_KEY=your_key
HELIUS_API_KEY=your_key
```

**Run**
```bash
# Start Dashboard
streamlit run dashboard_v3_dynamic.py

# Or use Windows script
run_gmt_pay_dashboard.bat
```

Access at `http://localhost:8501`

### 📁 Project Structure

```
gmt-pay-dashboard/
├── dashboard_v3_dynamic.py      # Main dashboard app
├── chain_data_fetcher.py        # On-chain data fetcher
├── analyze_vip_users.py         # User behavior analysis
├── auto_refresh_data.py         # Auto-refresh service
└── requirements.txt             # Dependencies
```

### 🎨 Tech Stack

- **Streamlit** - Web framework
- **Pandas** - Data processing
- **Plotly** - Data visualization
- **Etherscan API** - EVM chain data source
- **Helius API** - Solana chain data source

### 📊 Supported Blockchains & Tokens

| Blockchain | Supported Tokens |
|-----------|-----------------|
| 🔵 Ethereum | USDC, USDT |
| 🟡 BNB Chain | USDC, USDT, GGUSD, BUSD |
| 🟣 Polygon | USDC, USDT, GGUSD |
| 🌈 Solana | USDC, USDT |

### 📍 Monitored Wallet Addresses

All data is fetched from the following public on-chain wallet addresses:

**EVM Chains** (Ethereum/BNB/Polygon):
```
0x7a75eca169f67fcd4fe58b53a0b26e1ee774ca77
```

**Solana Chain**:
```
G7bMBQegH3RyRjt2QZu3o6BA2ZQQ7shdJ7zGrw7PwNEL
```

**Polygon Refund Address**:
```
0x6f724c70500d899883954a5ac2e6f38d25422f60
```

All data is fetched from public blockchain networks and can be verified on blockchain explorers.

### 🔄 Data Updates

- **On-chain Data**: 30-minute cache, auto-refresh on access
- **User Analytics**: Configurable periodic refresh
- **Manual Refresh**: "🔄 Refresh Data" button in sidebar

### 🛠️ Advanced Usage

**Run User Analysis**
```bash
python analyze_vip_users.py
```

**Start Auto-Refresh Service**
```bash
# Windows
start_with_auto_refresh.bat

# Linux/Mac
./start_with_auto_refresh.sh
```

**Docker Deployment**
```bash
docker-compose up -d
```

### 📝 Data Format

**Transaction Data Fields**
- Chain: Blockchain name
- Token: Payment token
- Amount: Payment amount (USD)
- Card_Value: Card face value
- DateTime: Transaction time (UTC)
- TxHash: Transaction hash

### 🙋 FAQ

**Q: Where does the data come from?**  
A: All data is fetched from public blockchain networks via Etherscan and Helius APIs.

**Q: How often does data update?**  
A: Default 30-minute cache, can be manually refreshed or configured for auto-refresh.

**Q: API rate limit issues?**  
A: Use paid API keys to increase call limits.

### 📄 License

MIT License

---

<a name="中文"></a>
## 中文

### 概述
GMT Pay卡片销售数据实时监控看板，支持多链、多代币数据聚合分析。

### ✨ 功能特性

**数据分析**
- **多链支持**: Ethereum、BNB Chain、Polygon、Solana
- **多代币**: USDC、USDT（所有链）、GGUSD（BNB/Polygon）、BUSD（BNB）
- **实时数据**: 自动从区块链抓取交易数据
- **可视化图表**: 销售趋势、链上分布、时间序列分析
- **用户分析**: 持有者行为追踪和统计

**其他特性**
- **多语言**: 中英文界面切换
- **自动刷新**: 数据定期更新（30分钟缓存）
- **交互式**: 时间范围筛选、数据导出

### 🚀 快速开始

**环境要求**
- Python 3.9+
- 区块链数据API Keys

**安装依赖**
```bash
pip install -r requirements.txt
```

**配置**
创建 `.env` 文件，配置API Keys：
```bash
ETHERSCAN_API_KEY=your_key
HELIUS_API_KEY=your_key
```

**启动**
```bash
# 启动Dashboard
streamlit run dashboard_v3_dynamic.py

# 或使用Windows快捷脚本
run_gmt_pay_dashboard.bat
```

访问 `http://localhost:8501`

### 📁 项目结构

```
gmt-pay-dashboard/
├── dashboard_v3_dynamic.py      # 主Dashboard应用
├── chain_data_fetcher.py        # 链上数据抓取
├── analyze_vip_users.py         # 用户行为分析
├── auto_refresh_data.py         # 自动刷新服务
└── requirements.txt             # 依赖包
```

### 🎨 技术栈

- **Streamlit** - Web应用框架
- **Pandas** - 数据处理
- **Plotly** - 数据可视化
- **Etherscan API** - EVM链数据源
- **Helius API** - Solana链数据源

### 📊 支持的区块链与代币

| 区块链 | 支持代币 |
|-------|---------|
| 🔵 Ethereum | USDC, USDT |
| 🟡 BNB Chain | USDC, USDT, GGUSD, BUSD |
| 🟣 Polygon | USDC, USDT, GGUSD |
| 🌈 Solana | USDC, USDT |

### 📍 监控的钱包地址

所有数据来自以下公开的链上钱包地址：

**EVM链** (Ethereum/BNB/Polygon):
```
0x7a75eca169f67fcd4fe58b53a0b26e1ee774ca77
```

**Solana链**:
```
G7bMBQegH3RyRjt2QZu3o6BA2ZQQ7shdJ7zGrw7PwNEL
```

**Polygon退款地址**:
```
0x6f724c70500d899883954a5ac2e6f38d25422f60
```

所有数据均从公开区块链网络获取，可在区块链浏览器上验证。

### 🔄 数据更新

- **链上数据**: 30分钟缓存，访问时自动刷新
- **用户分析**: 可配置定期刷新
- **手动刷新**: Dashboard侧边栏 "🔄 刷新数据" 按钮

### 🛠️ 高级功能

**运行用户分析脚本**
```bash
python analyze_vip_users.py
```

**启动自动刷新服务**
```bash
# Windows
start_with_auto_refresh.bat

# Linux/Mac
./start_with_auto_refresh.sh
```

**Docker部署**
```bash
docker-compose up -d
```

### 📝 数据格式

**交易数据字段**
- Chain: 区块链名称
- Token: 支付代币
- Amount: 支付金额（USD）
- Card_Value: 卡片面值
- DateTime: 交易时间（UTC）
- TxHash: 交易哈希

### 🙋 常见问题

**Q: 数据从哪里来？**  
A: 所有数据来自公开的区块链网络，通过Etherscan和Helius API实时抓取。

**Q: 数据多久更新？**  
A: 默认30分钟缓存，可手动刷新或配置自动刷新服务。

**Q: API限额问题？**  
A: 可以使用付费API Key提升调用限额。

### 📄 License

MIT License

---

**GMT Pay Dashboard** | Built with Streamlit & ❤️
