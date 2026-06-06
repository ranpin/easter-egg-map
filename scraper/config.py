"""彩蛋地图数据采集 - 配置文件"""
import os
from dotenv import load_dotenv

load_dotenv()

# 搜索关键词矩阵
SEARCH_KEYWORDS = {
    "xiaohongshu": [
        "旅行彩蛋", "景点藏宝", "旅途惊喜",
        "藏在景区的礼物", "旅行盲盒", "城市寻宝",
        "景区放书", "旅行宝藏"
    ],
    "douyin": [
        "旅行彩蛋", "景区隐藏惊喜", "在路上放了一本书",
        "旅行宝藏", "城市探险彩蛋", "景点盲盒"
    ]
}

# 采集频率控制（秒）
REQUEST_INTERVAL = 12  # 单IP每分钟≤5次
MAX_PAGES_PER_KEYWORD = 3  # 每个关键词最多翻页数

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scraped")

# 高德地图API（用于逆地理编码补全位置信息）
AMAP_KEY = os.getenv("AMAP_KEY", "")
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/regeo"
