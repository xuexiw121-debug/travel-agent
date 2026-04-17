import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..tools.search_attractions import search_attractions
from ..tools.plan_route import plan_route


class ItineraryService:
    """行程生成服务"""

    def __init__(self):
        self.breakfast_time = (9, 0)    # 9:00
        self.lunch_time = (12, 30)      # 12:30
        self.dinner_time = (18, 30)     # 18:30
        self.max_attractions_per_day = 4

    def generate_itinerary(
        self,
        destination: str,
        days: int,
        people: int = 1,
        preferences: Optional[str] = None
    ) -> Dict:
        """
        生成完整行程

        参数:
            destination: 目的地
            days: 天数
            people: 人数
            preferences: 偏好

        返回:
            完整行程数据
        """
        # 1. 搜索景点
        keywords = preferences.split(",") if preferences else []
        attractions = search_attractions(destination, keywords=keywords)

        if not attractions:
            return {"error": f"未找到 {destination} 的相关景点"}

        # 2. 筛选景点 (根据天数)
        selected = attractions[:min(len(attractions), days * self.max_attractions_per_day)]

        # 3. 规划路线
        route_result = plan_route(selected)

        # 4. 生成分日行程
        daily_itineraries = self._generate_daily_itineraries(
            route_result,
            days,
            people
        )

        return {
            "destination": destination,
            "days": days,
            "people": people,
            "preferences": preferences,
            "total_distance_km": route_result.get("total_distance_km", 0),
            "attractions": selected,
            "daily_itineraries": daily_itineraries
        }

    def _generate_daily_itineraries(
        self,
        route_result: Dict,
        days: int,
        people: int
    ) -> List[Dict]:
        """生成分日行程"""
        daily_routes = route_result.get("daily_routes", [])
        attractions = route_result.get("attractions_order", [])

        itineraries = []

        for day in range(1, days + 1):
            if day - 1 < len(daily_routes):
                day_attractions = daily_routes[day - 1]
                day_attraction_names = [attractions[i] for i in day_attractions]
            else:
                day_attraction_names = []

            itinerary = {
                "day": day,
                "theme": self._get_day_theme(day),
                "breakfast": self._recommend_breakfast(),
                "lunch": self._recommend_lunch(),
                "dinner": self._recommend_dinner(),
                "attractions": day_attraction_names,
                "tips": self._get_day_tips(day)
            }

            itineraries.append(itinerary)

        return itineraries

    def _get_day_theme(self, day: int) -> str:
        """获取每日主题"""
        themes = {
            1: "初识目的地 - 经典必游",
            2: "深度探索 - 文化之旅",
            3: "休闲放松 - 当地生活体验"
        }
        return themes.get(day, f"第{day}天 - 精彩行程")

    def _recommend_breakfast(self) -> Dict:
        """推荐早餐"""
        return {
            "suggestion": "当地特色早餐",
            "options": ["小巷早点", "茶餐厅", "酒店早餐"],
            "time": "8:30-9:30",
            "budget": "20-50元/人"
        }

    def _recommend_lunch(self) -> Dict:
        """推荐午餐"""
        return {
            "suggestion": "景区附近餐厅或当地美食",
            "options": ["特色餐厅", "小吃一条街", "商场美食广场"],
            "time": "12:00-13:30",
            "budget": "50-150元/人"
        }

    def _recommend_dinner(self) -> Dict:
        """推荐晚餐"""
        return {
            "suggestion": "体验当地夜生活",
            "options": ["观光夜市", "江景餐厅", "当地网红店"],
            "time": "18:00-20:00",
            "budget": "100-300元/人"
        }

    def _get_day_tips(self, day: int) -> List[str]:
        """获取每日提示"""
        tips = {
            1: ["早点出发避人流", "记得带好身份证件", "提前购买门票"],
            2: ["穿着舒适的步行鞋", "注意防晒或防雨", "适时休息"],
            3: ["可以睡个懒觉", "购买伴手礼", "提前规划返程"]
        }
        return tips.get(day, ["注意安全", "保管好财物"])

    def format_itinerary_text(self, itinerary: Dict) -> str:
        """格式化行程为可读文本"""
        lines = []

        lines.append("=" * 50)
        lines.append(f"  {itinerary['destination']} {itinerary['days']}天{itinerary['people']}人旅行行程")
        lines.append("=" * 50)
        lines.append("")

        for day_info in itinerary.get("daily_itineraries", []):
            lines.append(f"\n{'─' * 50}")
            lines.append(f"【第{day_info['day']}天】{day_info['theme']}")
            lines.append(f"{'─' * 50}")

            lines.append(f"\n🍳 早餐: {day_info['breakfast']['suggestion']}")
            lines.append(f"   ⏰ 时间: {day_info['breakfast']['time']}")

            lines.append(f"\n🏛️ 上午行程:")
            for attr in day_info.get("attractions", [])[:2]:
                lines.append(f"   • {attr}")

            lines.append(f"\n🍜 午餐: {day_info['lunch']['suggestion']}")
            lines.append(f"   ⏰ 时间: {day_info['lunch']['time']}")

            lines.append(f"\n🏛️ 下午行程:")
            for attr in day_info.get("attractions", [])[2:]:
                lines.append(f"   • {attr}")

            lines.append(f"\n🍽️ 晚餐: {day_info['dinner']['suggestion']}")
            lines.append(f"   ⏰ 时间: {day_info['dinner']['time']}")

            lines.append(f"\n💡 温馨提示:")
            for tip in day_info.get("tips", []):
                lines.append(f"   • {tip}")

        lines.append(f"\n{'=' * 50}")
        lines.append(f"📊 总行程距离: 约 {itinerary.get('total_distance_km', 0)} 公里")
        lines.append("=" * 50)

        return "\n".join(lines)


# 全局单例
_itinerary_service: Optional[ItineraryService] = None


def get_itinerary_service() -> ItineraryService:
    """获取全局行程服务实例"""
    global _itinerary_service
    if _itinerary_service is None:
        _itinerary_service = ItineraryService()
    return _itinerary_service
