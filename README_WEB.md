# 量化决策系统 v2.1 - Web版

一个基于Web的量化分析决策系统，支持行业/概念板块、中证指数和恒生科技等多种指数类型，提供丰富的技术指标、交互式图表可视化和信号检测功能。

## ✨ 新特性

### 🌐 Web版本优势
- **跨平台访问**：通过浏览器即可使用，无需安装客户端
- **现代化界面**：采用响应式设计，支持各种屏幕尺寸
- **高性能图表**：使用ECharts实现流畅的交互式图表
- **RESTful API**：提供完整的API接口，方便集成和扩展
- **多终端支持**：可在手机、平板、电脑上使用

### 🎯 核心功能
- **监控列表管理**：添加、删除、搜索多种类型的指数
- **数据自动更新**：支持单个或批量更新市场数据
- **技术指标分析**：RSI、MACD、KDJ、均线等多种指标
- **交易信号检测**：自动扫描并生成买入/卖出信号
- **图表可视化**：K线图、成交量、技术指标一体化展示
- **策略管理**：自定义交易策略，灵活配置买卖条件

## 🚀 快速开始

### 1. 环境要求
- Python 3.8 或更高版本
- 现代浏览器（Chrome、Firefox、Edge等）

### 2. 安装依赖

```powershell
# Windows
pip install -r requirements.txt

# Linux/Mac
pip3 install -r requirements.txt
```

### 3. 启动Web服务

#### Windows
```powershell
# 方法1：使用启动脚本（推荐）
start_web.bat

# 方法2：直接运行
python web_app.py
```

#### Linux/Mac
```bash
# 方法1：使用启动脚本（推荐）
chmod +x start_web.sh
./start_web.sh

# 方法2：直接运行
python3 web_app.py
```

### 4. 访问系统

启动成功后，在浏览器中访问：
```
http://localhost:5000
```

## 📖 使用指南

### 监控列表管理

#### 添加监控
1. 点击顶部工具栏的 **"➕ 添加监控"** 按钮
2. 输入指数代码/名称、显示名称
3. 选择类型（可自动检测）
4. 点击 **"确定"** 完成添加

#### 搜索指数
1. 点击 **"🔍 搜索指数"** 按钮
2. 输入关键字搜索
3. 点击搜索结果快速添加

#### 删除监控
1. 在监控列表中选择要删除的项目
2. 点击 **"❌ 移除监控"** 按钮
3. 确认删除

### 数据更新

#### 更新所有数据
点击 **"🔄 更新数据"** 按钮，系统将自动更新所有监控项的市场数据

#### 更新单个指数
1. 在监控列表中选择指数
2. 点击 **"查看"** 按钮
3. 数据会自动加载

### 图表分析

#### K线图
- 显示完整的OHLC K线数据
- 叠加MA5、MA20、MA60均线
- 底部显示成交量柱状图
- 支持缩放和拖动浏览

#### 技术指标
切换到"技术指标"标签页，查看：
- **RSI**：相对强弱指标，超买超卖信号
- **MACD**：趋势跟踪指标，金叉死叉信号
- **KDJ**：随机指标，短期买卖参考

#### 综合分析
查看指数的完整分析报告，包括：
- 最新价格和成交量
- 各项技术指标数值
- 当前交易信号建议

### 信号扫描

1. 点击 **"📊 扫描信号"** 按钮
2. 系统自动分析所有监控项
3. 在"交易信号"标签页查看结果
4. 信号包括买入(BUY)和卖出(SELL)建议

## 🔧 API接口文档

Web版提供完整的RESTful API接口，可用于：
- 第三方应用集成
- 自动化交易脚本
- 数据导出和分析
- 移动应用开发

### 主要API端点

#### 系统信息
```
GET /api/system/info
```

#### 监控列表
```
GET    /api/watchlist          # 获取监控列表
POST   /api/watchlist          # 添加监控项
DELETE /api/watchlist/{symbol} # 删除监控项
```

#### 数据管理
```
GET  /api/data/search?q={query}  # 搜索指数
POST /api/data/update             # 更新数据
GET  /api/data/market/{symbol}    # 获取市场数据
```

#### 信号分析
```
POST /api/signals/scan           # 扫描信号
GET  /api/signals/{symbol}       # 获取指数信号
GET  /api/analysis/{symbol}      # 分析指数
```

#### 图表数据
```
GET /api/chart/{symbol}?days=250 # 获取图表数据
```

### API响应格式
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... },
  "timestamp": "2025-10-09T12:00:00"
}
```

## 📊 支持的指数类型

### 行业板块（Industry）
- 代码格式：BK开头或板块名称
- 示例：BK0001、新能源汽车、半导体等

### 概念板块（Concept）
- 代码格式：板块名称
- 示例：人工智能、元宇宙、碳中和等

### 中证指数（CSIndex）
- 代码格式：93开头的6位数字
- 示例：931643（中证白酒）、931643等

### 恒生科技（HK Tech）
- 香港恒生科技指数相关
- 示例：恒生科技指数等

## 🎨 技术指标说明

### 移动平均线（MA）
- **MA5**：5日均线，短期趋势
- **MA20**：20日均线，中期趋势
- **MA60**：60日均线，长期趋势

### 相对强弱指标（RSI）
- 范围：0-100
- **超卖区**：< 30，可能反弹
- **超买区**：> 70，可能回调

### MACD指标
- **MACD线**：快慢线差值
- **Signal线**：MACD的平滑线
- **Histogram**：MACD与Signal的差值
- **金叉**：MACD上穿Signal，买入信号
- **死叉**：MACD下穿Signal，卖出信号

### KDJ指标
- **K线**：快速随机指标
- **D线**：K的移动平均
- **J线**：3K-2D
- **超卖**：J < 20
- **超买**：J > 80

## ⚙️ 配置文件

### 策略配置
位置：`config/strategies.json`

自定义交易策略示例：
```json
{
  "strategies": [
    {
      "name": "RSI策略",
      "buy_expression": "RSI(14) < 30",
      "sell_expression": "RSI(14) > 70"
    }
  ]
}
```

### 监控列表
位置：`config/watchlist.json`

保存用户添加的监控项

## 🗂️ 项目结构

```
QuanAnalysis/
├── web_app.py              # Web服务主程序
├── start_web.bat           # Windows启动脚本
├── start_web.sh            # Linux/Mac启动脚本
├── requirements.txt        # 依赖包列表
├── web_static/            # Web前端资源
│   ├── index.html         # 主页面
│   ├── style.css          # 样式表
│   └── app.js             # JavaScript逻辑
├── config/                # 配置文件
│   ├── strategies.json    # 策略配置
│   └── watchlist.json     # 监控列表
├── data/                  # 数据存储
│   └── quant_analysis.db  # SQLite数据库
├── src/                   # 核心业务逻辑
│   ├── data_fetcher.py    # 数据获取
│   ├── strategy_manager.py # 策略管理
│   └── expression_parser.py # 表达式解析
├── indicators/            # 技术指标
│   └── technical_indicators.py
└── utils/                 # 工具模块
    └── database.py        # 数据库操作
```

## 🔍 常见问题

### Q: 无法访问Web界面？
A: 请检查：
1. Python服务是否正常启动
2. 防火墙是否阻止5000端口
3. 浏览器地址是否正确：http://localhost:5000

### Q: 数据更新失败？
A: 可能原因：
1. 网络连接问题
2. AKShare数据源暂时不可用
3. 指数代码错误，请检查代码格式

### Q: 图表显示异常？
A: 解决方法：
1. 清除浏览器缓存
2. 使用Chrome或Firefox等现代浏览器
3. 检查控制台是否有JavaScript错误

### Q: API调用失败？
A: 检查项：
1. Web服务是否运行
2. API地址是否正确
3. 查看控制台日志了解详细错误

## 📝 更新日志

### v2.1 Web版 (2025-10-09)
- ✨ 全面改造为Web架构
- 🚀 使用Flask提供RESTful API
- 🎨 现代化Web界面设计
- 📊 ECharts交互式图表
- 🔧 完整的API接口文档
- 📱 响应式设计支持多终端

### v2.0 GUI版
- 基于Tkinter的桌面GUI应用
- matplotlib图表可视化
- 多指数类型支持

## 🛠️ 技术栈

### 后端
- **Flask**: Web框架
- **AKShare**: 数据获取
- **Pandas**: 数据处理
- **SQLite**: 数据存储

### 前端
- **HTML5/CSS3**: 页面结构和样式
- **JavaScript (ES6+)**: 交互逻辑
- **ECharts**: 图表可视化

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: your-email@example.com

---

**版本**: v2.1 Web版  
**更新日期**: 2025-10-09  
**开发团队**: 量化决策系统团队
