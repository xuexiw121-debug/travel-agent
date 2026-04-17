import json
import os
from pathlib import Path
from typing import List, Dict, Optional

# 景点数据库路径
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ATTRACTIONS_FILE = DATA_DIR / "attractions.json"


def load_attractions() -> List[Dict]:
    """加载景点数据库"""
    if ATTRACTIONS_FILE.exists():
        with open(ATTRACTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def search_attractions(
    destination: str,
    category: Optional[str] = None,
    keywords: Optional[List[str]] = None
) -> List[Dict]:
    """
    搜索景点工具

    参数:
        destination: 目的地城市
        category: 景点类别 (natural, cultural, theme_park, food, shopping)
        keywords: 关键词列表

    返回:
        匹配的景点列表
    """
    attractions = load_attractions()

    # 筛选目的地
    results = [a for a in attractions if destination in a.get("city", "") or destination in a.get("name", "")]

    # 按类别筛选
    if category:
        results = [a for a in results if a.get("category") == category]

    # 按关键词筛选
    if keywords:
        filtered = []
        for a in results:
            text = f"{a.get('name', '')} {a.get('description', '')} {' '.join(a.get('tags', []))}"
            if any(kw in text for kw in keywords):
                filtered.append(a)
        results = filtered

    # 如果数据库为空，返回模拟数据
    if not results:
        results = _get_mock_attractions(destination, category, keywords)

    return results


def _get_mock_attractions(destination: str, category: Optional[str], keywords: Optional[List[str]]) -> List[Dict]:
    """当数据库为空时返回模拟景点数据"""
    mock_data = {
        "上海": [
            {"id": 1, "name": "外滩", "city": "上海", "category": "cultural", "rating": 4.8,
             "description": "上海的标志性景点，浦西万国建筑博览群", "duration": "2小时", "ticket": "免费",
             "tags": ["夜景", "地标", "拍照"], "coordinates": {"lat": 31.2405, "lng": 121.4901},
             "hours": "全天", "best_time": "傍晚"},
            {"id": 2, "name": "东方明珠塔", "city": "上海", "category": "theme_park", "rating": 4.6,
             "description": "上海标志性建筑，观光塔", "duration": "3小时", "ticket": "180元",
             "tags": ["观光", "地标", "夜景"], "coordinates": {"lat": 31.2397, "lng": 121.4998},
             "hours": "9:00-21:00", "best_time": "傍晚"},
            {"id": 3, "name": "上海迪士尼乐园", "city": "上海", "category": "theme_park", "rating": 4.7,
             "description": "国际知名主题公园", "duration": "1天", "ticket": "399元",
             "tags": ["亲子", "游乐", "主题公园"], "coordinates": {"lat": 31.1429, "lng": 121.6570},
             "hours": "8:30-20:00", "best_time": "全天"},
            {"id": 4, "name": "豫园", "city": "上海", "category": "cultural", "rating": 4.5,
             "description": "江南古典园林", "duration": "2小时", "ticket": "40元",
             "tags": ["园林", "历史", "文化"], "coordinates": {"lat": 31.2277, "lng": 121.4899},
             "hours": "9:00-17:00", "best_time": "早晨"},
            {"id": 5, "name": "田子坊", "city": "上海", "category": "shopping", "rating": 4.4,
             "description": "老上海石库门风情街区", "duration": "2-3小时", "ticket": "免费",
             "tags": ["文艺", "购物", "美食"], "coordinates": {"lat": 31.2154, "lng": 121.4732},
             "hours": "全天", "best_time": "下午"},
        ],
        "北京": [
            {"id": 101, "name": "故宫", "city": "北京", "category": "cultural", "rating": 4.9,
             "description": "明清两代皇宫，世界上现存规模最大的宫殿建筑群", "duration": "4-5小时", "ticket": "60元",
             "tags": ["历史", "文化", "地标"], "coordinates": {"lat": 39.9163, "lng": 116.3972},
             "hours": "8:30-17:00", "best_time": "上午"},
            {"id": 102, "name": "长城", "city": "北京", "category": "natural", "rating": 4.8,
             "description": "世界七大奇迹之一", "duration": "半天到一天", "ticket": "40-65元",
             "tags": ["历史", "户外", "地标"], "coordinates": {"lat": 40.4319, "lng": 116.5704},
             "hours": "7:00-18:00", "best_time": "早晨"},
            {"id": 103, "name": "颐和园", "city": "北京", "category": "cultural", "rating": 4.7,
             "description": "中国现存最大的皇家园林", "duration": "3-4小时", "ticket": "30元",
             "tags": ["园林", "历史", "休闲"], "coordinates": {"lat": 39.9993, "lng": 116.4661},
             "hours": "6:30-19:00", "best_time": "上午"},
            {"id": 104, "name": "天坛", "city": "北京", "category": "cultural", "rating": 4.6,
             "description": "明清帝王祭天的场所", "duration": "2小时", "ticket": "34元",
             "tags": ["历史", "建筑", "文化"], "coordinates": {"lat": 39.8760, "lng": 116.4106},
             "hours": "6:00-21:00", "best_time": "早晨"},
        ],
        "成都": [
            {"id": 201, "name": "大熊猫繁育研究基地", "city": "成都", "category": "natural", "rating": 4.8,
             "description": "观赏大熊猫的最佳地点", "duration": "3-4小时", "ticket": "55元",
             "tags": ["亲子", "动物", "自然"], "coordinates": {"lat": 30.7378, "lng": 104.1448},
             "hours": "7:30-18:00", "best_time": "上午"},
            {"id": 202, "name": "宽窄巷子", "city": "成都", "category": "cultural", "rating": 4.5,
             "description": "清朝古街道，成都名片", "duration": "2-3小时", "ticket": "免费",
             "tags": ["美食", "购物", "文化"], "coordinates": {"lat": 30.6598, "lng": 104.0562},
             "hours": "全天", "best_time": "傍晚"},
            {"id": 203, "name": "武侯祠", "city": "成都", "category": "cultural", "rating": 4.5,
             "description": "纪念诸葛亮的三国历史博物馆", "duration": "2小时", "ticket": "50元",
             "tags": ["历史", "文化", "三国"], "coordinates": {"lat": 30.6517, "lng": 104.0452},
             "hours": "8:00-20:00", "best_time": "上午"},
        ]
    }

    # 获取目的地的模拟数据
    results = mock_data.get(destination, [])

    # 按类别筛选
    if category:
        results = [a for a in results if a.get("category") == category]

    # 按关键词筛选
    if keywords:
        filtered = []
        for a in results:
            text = f"{a.get('name', '')} {a.get('description', '')} {' '.join(a.get('tags', []))}"
            if any(kw in text for kw in keywords):
                filtered.append(a)
        results = filtered

    return results


if __name__ == "__main__":
    # 测试
    results = search_attractions("上海", keywords=["亲子"])
    for r in results:
        print(f"- {r['name']}: {r['description']}")
