#!/bin/bash
# 彩蛋地图 - MediaCrawler 一键启动脚本
# 使用方法: bash run_crawler.sh [平台] [关键词]
# 示例: bash run_crawler.sh xhs "课本接头,人民币打卡"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
MC_SRC="$SCRIPT_DIR/mediactawler_src"

# 检查虚拟环境
if [ ! -d "$VENV" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv .venv && .venv/bin/pip install -r mediactawler_src/requirements.txt"
    exit 1
fi

# 默认参数
PLATFORM="${1:-xhs}"
KEYWORDS="${2:-课本接头计划,景点藏课本,人民币打卡,漂流相机,文化礼物交换}"

echo "🚀 启动 MediaCrawler"
echo "   平台: $PLATFORM"
echo "   关键词: $KEYWORDS"
echo "   数据保存: $SCRIPT_DIR/output/"
echo ""

# 创建输出目录
mkdir -p "$SCRIPT_DIR/output"

# 设置环境变量覆盖MediaCrawler默认配置
export MEDIAMCRAWLER_PLATFORM="$PLATFORM"
export MEDIAMCRAWLER_KEYWORDS="$KEYWORDS"
export MEDIAMCRAWLER_SAVE_DATA_OPTION="json"
export MEDIAMCRAWLER_SAVE_DATA_PATH="$SCRIPT_DIR/output"
export MEDIAMCRAWLER_HEADLESS="False"
export MEDIAMCRAWLER_LOGIN_TYPE="qrcode"
export MEDIAMCRAWLER_CRAWLER_TYPE="search"
export MEDIAMCRAWLER_MAX_NOTES_COUNT="30"
export MEDIAMCRAWLER_ENABLE_GET_MEIDAS="True"

cd "$MC_SRC"

echo "⚠️  即将打开浏览器，请扫码登录小红书..."
echo "   登录后Cookie会自动保存，下次无需重复登录"
echo ""

"$VENV/bin/python" main.py --platform "$PLATFORM" --lt qrcode --type search

echo ""
echo "✅ 采集完成！数据保存在: $SCRIPT_DIR/output/"
echo "   运行 post_processor.py 清洗数据:"
echo "   $VENV/bin/python $SCRIPT_DIR/post_processor.py"
