# 🕷️ 彩蛋地图 - 自动化数据采集系统

## 架构概览

本采集系统基于 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)（30K+ Star）构建，支持小红书和抖音的旅行彩蛋内容自动采集。

```
┌─────────────────────────────────────────────┐
│              main.py (调度入口)               │
├──────────────┬──────────────────────────────┤
│  xhs_worker  │       douyin_worker          │
│  (小红书采集) │       (抖音采集)              │
├──────────────┴──────────────────────────────┤
│         MediaCrawler (底层引擎)              │
│   Playwright + Cookie管理 + 反检测           │
├─────────────────────────────────────────────┤
│      post_processor.py (数据清洗/AI分类)     │
├─────────────────────────────────────────────┤
│         output/ (JSON结构化输出)             │
└─────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

```bash
# Python 3.8+
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置Cookie

首次使用需要手动登录获取Cookie：

```bash
python login_helper.py --platform xhs    # 小红书登录
python login_helper.py --platform dy     # 抖音登录
```

浏览器会弹出，手动扫码/账密登录后Cookie自动保存到 `cookies/` 目录。

### 3. 运行采集

```bash
# 采集全部平台
python main.py

# 仅采集小红书
python main.py --platform xhs --keywords "旅行彩蛋,景点藏宝,课本接头"

# 仅采集抖音
python main.py --platform dy --keywords "城市寻宝,旅行惊喜"

# 指定采集数量
python main.py --platform xhs --max-notes 50
```

### 4. 定时采集（可选）

```bash
# 每天凌晨3点自动采集
crontab -e
0 3 * * * cd /path/to/scraper && python main.py >> logs/cron.log 2>&1
```

## 搜索关键词配置

在 `config.yaml` 中配置采集关键词：

```yaml
search_keywords:
  xhs:
    - "旅行彩蛋"
    - "景点藏宝"
    - "课本接头计划"
    - "城市寻宝"
    - "旅途惊喜"
    - "藏在景区的书"
    - "国家地理杂志 旅行"
  douyin:
    - "旅行彩蛋"
    - "景点隐藏惊喜"
    - "城市寻宝"
    - "课本接头"
    - "宝藏景点"
```

## 输出格式

采集结果保存在 `output/` 目录，每条数据结构：

```json
{
  "id": "unique_id",
  "title": "笔记标题",
  "description": "正文内容",
  "category": "book|magazine|letter|blindbox|art|other",
  "regionTag": "national_geo|world_geo|three_mountains|five_peaks|...",
  "latitude": 30.0,
  "longitude": 120.0,
  "locationName": "具体地点",
  "city": "城市",
  "province": "省份",
  "previewImage": "图片URL",
  "sourcePlatform": "xiaohongshu|douyin",
  "sourceUrl": "原始链接",
  "sourceAuthor": "作者昵称",
  "likes": 1234,
  "collectedAt": "2026-06-06T12:00:00"
}
```

## ⚠️ 合规提醒

- 仅采集公开可见内容，不突破登录墙
- 控制采集频率（默认间隔3-8秒随机延迟）
- 所有数据标注来源平台和原作者
- 提供"删除我的内容"入口
- 遵守 robots.txt 和平台服务条款
