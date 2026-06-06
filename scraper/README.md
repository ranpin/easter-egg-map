# 🕷️ 彩蛋地图数据采集工具

从小红书、抖音等平台自动采集"旅行彩蛋"相关内容，结构化输出为 JSON 数据。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt
playwright install chromium

# 2. 运行全部采集器
python main.py

# 3. 仅采集小红书
python main.py --platform xhs

# 4. 仅采集抖音
python main.py --platform dy
```

## 输出格式

采集结果保存在 `../data/scraped/` 目录，JSON 格式：

```json
[
  {
    "title": "在大理古城藏了一本国家地理",
    "description": "...",
    "category": "杂志",
    "images": ["https://..."],
    "location_name": "大理古城",
    "city": "大理",
    "source_url": "https://www.xiaohongshu.com/...",
    "source_platform": "xiaohongshu",
    "source_author": "旅行者小王",
    "placed_at": "2026-06-01T10:30:00"
  }
]
```

## ⚠️ 合规须知

- 仅采集公开可见内容，不突破登录墙
- 单IP每分钟≤5次请求，避免对平台造成压力
- 所有采集内容明确标注来源平台和原作者
- 提供"删除我的内容"入口，响应权利人下架请求
- 不采集用户隐私信息（手机号、真实姓名等）
- 请遵守各平台的 robots.txt 和服务条款

## 文件结构

```
scraper/
├── main.py              # 主入口，统一调度
├── config.py            # 配置（关键词、频率、API Key）
├── models.py            # Pydantic 数据模型
├── xhs_scraper.py       # 小红书采集器
├── douyin_scraper.py    # 抖音采集器
├── requirements.txt     # Python 依赖
└── README.md            # 本文件
```
