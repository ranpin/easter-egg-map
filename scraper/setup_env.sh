#!/bin/bash
# 彩蛋地图采集系统 - 一键环境搭建脚本
# 解决 MediaCrawler 上游 pyproject.toml 与新版 setuptools 不兼容的问题
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
MC_SRC="$SCRIPT_DIR/mediactawler_src"

echo "🔧 开始搭建采集环境..."

# 1. 创建虚拟环境
if [ ! -d "$VENV" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv "$VENV"
fi

# 2. 升级 pip + 安装基础依赖
echo "📦 安装基础依赖..."
"$VENV/bin/pip" install --upgrade pip -q
"$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q

# 3. 安装 Playwright 浏览器引擎
echo "🌐 安装 Playwright Chromium..."
"$VENV/bin/playwright" install chromium

# 4. 克隆并安装 MediaCrawler（绕过 build isolation）
if [ ! -d "$MC_SRC/.git" ]; then
    echo "📥 克隆 MediaCrawler..."
    git clone --depth 1 https://github.com/NanmiCoder/MediaCrawler.git "$MC_SRC"
else
    echo "✅ MediaCrawler 已存在，跳过克隆"
fi

echo "📦 安装 MediaCrawler（--no-build-isolation）..."
"$VENV/bin/pip" install "setuptools<75" -q
"$VENV/bin/pip" install --no-build-isolation -e "$MC_SRC" -q

echo ""
echo "✅ 环境搭建完成！"
echo ""
echo "启动采集："
echo "  bash run_crawler.sh xhs \"课本接头计划,景点藏课本,人民币打卡\""
echo ""
