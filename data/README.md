# 数据目录

此目录用于存储SQLite数据库文件。

数据库文件会在首次运行时自动创建：
- `quant_analysis.db` - 主数据库文件

## 数据库表结构

### watchlist - 监控列表
- 存储需要监控的指数信息

### market_data - 市场数据  
- 存储历史行情数据（OHLCV）

### signals - 交易信号
- 存储检测到的买卖信号记录
