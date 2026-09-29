#!/bin/bash
# 量化决策系统 Web版 - Linux/Mac启动脚本

echo "================================================"
echo "量化决策系统 Web版 启动中..."
echo "================================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "[1/3] 检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "Flask未安装，正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败，请手动运行: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo "[2/3] 启动Web服务..."
echo ""
echo "================================================"
echo "服务地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo "================================================"
echo ""

# 启动Flask应用
python3 web_app.py
