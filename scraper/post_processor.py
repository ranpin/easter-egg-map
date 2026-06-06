"""
数据后处理器 - AI分类 + 地理编码 + 结构化输出
将原始采集数据转换为彩蛋地图标准格式
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml


# 分类关键词映射（规则引擎，无需AI即可工作）
CATEGORY_KEYWORDS = {
    "book": ["书", "课本", "教材", "教科书", "阅读", "诗集", "小说", "边城", "日记", "书签"],
    "magazine": ["杂志", "国家地理", "世界地理", "期刊", "画报"],
    "letter": ["信", "手写", "祝福", "情书", "留言", "纸条", "祈福", "丝带"],
    "blindbox": ["盲盒", "惊喜", "礼物", "宝藏", "寻宝", "彩蛋"],
    "art": ["手绘", "明信片", "摄影", "画作", "艺术品", "胶片", "相机", "作品"],
}

REGION_KEYWORDS = {
    "national_geo": ["国家地理", "国家推荐", "国家级"],
    "world_geo": ["世界地理", "世界遗产", "UNESCO", "联合国"],
    "three_mountains": ["黄山", "庐山", "雁荡山", "三山"],
    "five_peaks": ["泰山", "华山", "衡山", "嵩山", "恒山", "五岳"],
    "world_heritage": ["故宫", "长城", "兵马俑", "莫高窟", "世界遗产", "古城"],
    "ancient_towns": ["古镇", "古城", "水乡", "丽江", "大理", "乌镇", "凤凰", "西塘", "周庄"],
    "coastal": ["海", "沙滩", "鼓浪屿", "三亚", "青岛", "厦门", "海滨", "栈桥"],
    "city_walk": ["citywalk", "城市漫步", "武康路", "南锣鼓巷", "玉林路", "胡同", "老街"],
    "hidden_gem": ["小众", "秘境", "隐藏", "冷门", "人少"],
}


def classify_category(text: str) -> str:
    """基于关键词规则分类彩蛋类型"""
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score
    return max(scores, key=scores.get) if scores else "other"


def classify_region(text: str) -> str:
    """基于关键词规则分类景点区域"""
    text_lower = text.lower()
    scores = {}
    for region, keywords in REGION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[region] = score
    return max(scores, key=scores.get) if scores else "hidden_gem"


def extract_location(text: str) -> Dict[str, str]:
    """从文本中提取地理位置信息（简单正则）"""
    result = {"locationName": "", "city": "", "province": ""}

    # 常见地名模式
    city_patterns = [
        r'(?:在|到|去了?)([\u4e00-\u9fa5]{2,4}(?:市|县|区|镇))',
        r'([\u4e00-\u9fa5]{2,4}(?:古城|古镇|景区|公园|山|峰|岛))',
    ]
    for pattern in city_patterns:
        match = re.search(pattern, text)
        if match:
            result["locationName"] = match.group(1)
            break

    return result


def process_raw_note(raw: Dict, platform: str) -> Dict:
    """将原始笔记数据转换为标准彩蛋格式"""
    title = raw.get("title", "") or raw.get("desc", "") or ""
    desc = raw.get("desc", "") or raw.get("content", "") or ""
    full_text = f"{title} {desc}"

    # 提取图片
    images = raw.get("image_list", []) or raw.get("images", [])
    preview_image = ""
    if images:
        first_img = images[0]
        if isinstance(first_img, dict):
            preview_image = first_img.get("url", "") or first_img.get("info_list", [{}])[0].get("url", "")
        elif isinstance(first_img, str):
            preview_image = first_img

    # 提取互动数据
    interact = raw.get("interact_info", {}) or {}
    likes = int(interact.get("liked_count", "0") or raw.get("digg_count", 0) or 0)

    return {
        "id": raw.get("note_id", "") or raw.get("aweme_id", "") or raw.get("id", ""),
        "title": title[:100],
        "description": desc[:500],
        "category": classify_category(full_text),
        "regionTag": classify_region(full_text),
        "latitude": None,  # 需要地理编码补充
        "longitude": None,
        "locationName": "",
        "city": "",
        "province": "",
        "previewImage": preview_image,
        "sourcePlatform": platform,
        "sourceUrl": raw.get("url", "") or raw.get("share_url", ""),
        "sourceAuthor": raw.get("user", {}).get("nickname", "") if isinstance(raw.get("user"), dict) else "",
        "likes": likes,
        "collectedAt": datetime.now().isoformat(),
    }


def geocode_batch(eggs: List[Dict], api_key: Optional[str] = None) -> List[Dict]:
    """批量地理编码（使用高德API或Nominatim降级）"""
    import requests

    for egg in eggs:
        location = egg.get("locationName", "")
        if not location or (egg.get("latitude") and egg.get("longitude")):
            continue

        try:
            if api_key:
                # 高德地理编码
                resp = requests.get(
                    "https://restapi.amap.com/v3/geocode/geo",
                    params={"address": location, "key": api_key},
                    timeout=5
                )
                data = resp.json()
                if data.get("geocodes"):
                    geo = data["geocodes"][0]
                    lng, lat = geo["location"].split(",")
                    egg["latitude"] = float(lat)
                    egg["longitude"] = float(lng)
                    egg["city"] = geo.get("city", "")
                    egg["province"] = geo.get("province", "")
            else:
                # Nominatim降级
                resp = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": location, "format": "json", "limit": 1},
                    headers={"User-Agent": "EasterEggMap/1.0"},
                    timeout=5
                )
                results = resp.json()
                if results:
                    egg["latitude"] = float(results[0]["lat"])
                    egg["longitude"] = float(results[0]["lon"])
        except Exception as e:
            print(f"  ⚠️ 地理编码失败 [{location}]: {e}")

    return eggs


def process_all(input_dir: str, output_dir: str, config_path: str = None):
    """处理所有原始采集数据"""
    config = {}
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    api_key = None
    geocoding_cfg = config.get("geocoding", {})
    env_var = geocoding_cfg.get("api_key_env", "")
    if env_var:
        api_key = os.environ.get(env_var)

    os.makedirs(output_dir, exist_ok=True)
    all_eggs = []

    for fname in sorted(Path(input_dir).glob("*.json")):
        if "processed" in fname.name:
            continue
        print(f"📂 处理: {fname.name}")
        with open(fname, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        platform = "xiaohongshu" if "xhs" in fname.name else "douyin"
        notes = raw_data if isinstance(raw_data, list) else raw_data.get("notes", [])

        for note in notes:
            egg = process_raw_note(note, platform)
            if egg["id"]:
                all_eggs.append(egg)

    # 去重
    seen = set()
    unique = []
    for egg in all_eggs:
        if egg["id"] not in seen:
            seen.add(egg["id"])
            unique.append(egg)

    # 地理编码
    print(f"\n🗺️ 地理编码中... ({len(unique)} 条)")
    unique = geocode_batch(unique, api_key)

    # 保存
    output_path = os.path.join(output_dir, f"processed_eggs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 处理完成! {len(unique)} 条 → {output_path}")
    return unique


if __name__ == "__main__":
    import sys
    input_d = sys.argv[1] if len(sys.argv) > 1 else "./output"
    output_d = sys.argv[2] if len(sys.argv) > 2 else "./output"
    process_all(input_d, output_d, "./config.yaml")
