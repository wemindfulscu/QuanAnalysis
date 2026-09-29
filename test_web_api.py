"""
Web版API测试脚本
用于验证量化决策系统Web版的API功能
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000/api"
TIMEOUT = 10

def print_header(title):
    """打印测试标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_system_info():
    """测试系统信息接口"""
    print_header("测试 1: 系统信息")
    try:
        response = requests.get(f"{BASE_URL}/system/info", timeout=TIMEOUT)
        data = response.json()
        
        if data['success']:
            print("✓ 系统信息获取成功")
            print(f"  版本: {data['data']['version']}")
            print(f"  监控项数: {data['data']['watchlist_count']}")
            print(f"  策略数: {data['data']['strategy_count']}")
            return True
        else:
            print("✗ 系统信息获取失败:", data.get('message'))
            return False
    except Exception as e:
        print(f"✗ 系统信息测试失败: {e}")
        return False

def test_watchlist():
    """测试监控列表接口"""
    print_header("测试 2: 监控列表")
    try:
        # 获取列表
        response = requests.get(f"{BASE_URL}/watchlist", timeout=TIMEOUT)
        data = response.json()
        
        if data['success']:
            print(f"✓ 监控列表获取成功，共 {len(data['data'])} 项")
            if data['data']:
                print("  示例项目:")
                item = data['data'][0]
                print(f"    - {item['name']} ({item['symbol']}) [{item['type']}]")
            return True
        else:
            print("✗ 监控列表获取失败:", data.get('message'))
            return False
    except Exception as e:
        print(f"✗ 监控列表测试失败: {e}")
        return False

def test_add_remove_watchlist():
    """测试添加和删除监控项"""
    print_header("测试 3: 添加/删除监控项")
    
    test_symbol = "TEST_API_" + datetime.now().strftime("%Y%m%d%H%M%S")
    test_name = "API测试项目"
    
    try:
        # 添加测试项
        print(f"添加测试项: {test_symbol}")
        response = requests.post(
            f"{BASE_URL}/watchlist",
            json={
                "symbol": test_symbol,
                "name": test_name,
                "type": "industry"
            },
            timeout=TIMEOUT
        )
        data = response.json()
        
        if data['success']:
            print("✓ 添加监控项成功")
        else:
            print("✗ 添加监控项失败:", data.get('message'))
            return False
        
        # 等待一下
        time.sleep(0.5)
        
        # 删除测试项
        print(f"删除测试项: {test_symbol}")
        response = requests.delete(
            f"{BASE_URL}/watchlist/{test_symbol}",
            timeout=TIMEOUT
        )
        data = response.json()
        
        if data['success']:
            print("✓ 删除监控项成功")
            return True
        else:
            print("✗ 删除监控项失败:", data.get('message'))
            return False
            
    except Exception as e:
        print(f"✗ 添加/删除测试失败: {e}")
        return False

def test_search():
    """测试搜索功能"""
    print_header("测试 4: 搜索功能")
    try:
        response = requests.get(
            f"{BASE_URL}/data/search?q=新能源&type=industry",
            timeout=TIMEOUT
        )
        data = response.json()
        
        if data['success']:
            results = data['data']
            print(f"✓ 搜索成功，找到 {len(results)} 个结果")
            if results:
                print("  示例结果:")
                for item in results[:3]:
                    print(f"    - {item['name']} ({item['symbol']}) [{item['type']}]")
            return True
        else:
            print("✗ 搜索失败:", data.get('message'))
            return False
    except Exception as e:
        print(f"✗ 搜索测试失败: {e}")
        return False

def test_strategies():
    """测试策略管理"""
    print_header("测试 5: 策略管理")
    try:
        response = requests.get(f"{BASE_URL}/strategies", timeout=TIMEOUT)
        data = response.json()
        
        if data['success']:
            strategies = data['data']
            print(f"✓ 策略列表获取成功，共 {len(strategies)} 个策略")
            if strategies:
                print("  已配置策略:")
                for strategy in strategies:
                    print(f"    - {strategy['name']}")
            return True
        else:
            print("✗ 策略列表获取失败:", data.get('message'))
            return False
    except Exception as e:
        print(f"✗ 策略测试失败: {e}")
        return False

def test_market_data():
    """测试市场数据获取"""
    print_header("测试 6: 市场数据")
    
    # 先获取监控列表
    try:
        response = requests.get(f"{BASE_URL}/watchlist", timeout=TIMEOUT)
        watchlist = response.json()['data']
        
        if not watchlist:
            print("⚠ 监控列表为空，跳过市场数据测试")
            return True
        
        # 获取第一个项目的数据
        symbol = watchlist[0]['symbol']
        print(f"获取 {watchlist[0]['name']} 的市场数据...")
        
        response = requests.get(
            f"{BASE_URL}/data/market/{symbol}?days=30",
            timeout=TIMEOUT
        )
        data = response.json()
        
        if data['success']:
            records = data['data']
            print(f"✓ 市场数据获取成功，共 {len(records)} 条记录")
            if records:
                latest = records[-1]
                print(f"  最新数据日期: {latest.get('date', 'N/A')}")
                print(f"  收盘价: {latest.get('close', 'N/A')}")
            return True
        else:
            print("✗ 市场数据获取失败:", data.get('message'))
            return False
            
    except Exception as e:
        print(f"✗ 市场数据测试失败: {e}")
        return False

def test_chart_data():
    """测试图表数据"""
    print_header("测试 7: 图表数据")
    
    try:
        # 获取监控列表
        response = requests.get(f"{BASE_URL}/watchlist", timeout=TIMEOUT)
        watchlist = response.json()['data']
        
        if not watchlist:
            print("⚠ 监控列表为空，跳过图表数据测试")
            return True
        
        # 获取第一个项目的图表数据
        symbol = watchlist[0]['symbol']
        print(f"获取 {watchlist[0]['name']} 的图表数据...")
        
        response = requests.get(
            f"{BASE_URL}/chart/{symbol}?days=100",
            timeout=TIMEOUT
        )
        data = response.json()
        
        if data['success']:
            chart_data = data['data']
            print("✓ 图表数据获取成功")
            print(f"  日期数: {len(chart_data.get('dates', []))}")
            print(f"  OHLCV数据: {len(chart_data.get('ohlcv', []))} 条")
            print(f"  MA5数据: {len([x for x in chart_data.get('ma', {}).get('ma5', []) if x is not None])} 条")
            print(f"  RSI数据: {len([x for x in chart_data.get('rsi', []) if x is not None])} 条")
            return True
        else:
            print("✗ 图表数据获取失败:", data.get('message'))
            return False
            
    except Exception as e:
        print(f"✗ 图表数据测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  量化决策系统 Web版 API测试")
    print("="*60)
    print(f"\n测试目标: {BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查服务是否可访问
    print("\n检查Web服务...")
    try:
        response = requests.get(BASE_URL.replace('/api', ''), timeout=5)
        if response.status_code == 200:
            print("✓ Web服务正常运行")
        else:
            print(f"✗ Web服务响应异常: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 无法连接到Web服务: {e}")
        print("\n请确保:")
        print("1. Web服务已启动 (python web_app.py)")
        print("2. 服务地址正确 (http://localhost:5000)")
        print("3. 防火墙未阻止连接")
        return
    
    # 运行测试
    results = []
    tests = [
        ("系统信息", test_system_info),
        ("监控列表", test_watchlist),
        ("添加/删除", test_add_remove_watchlist),
        ("搜索功能", test_search),
        ("策略管理", test_strategies),
        ("市场数据", test_market_data),
        ("图表数据", test_chart_data)
    ]
    
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
        time.sleep(0.5)  # 避免请求过快
    
    # 打印总结
    print_header("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常。")
    else:
        print(f"\n⚠ {total - passed} 个测试失败，请检查错误信息。")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
