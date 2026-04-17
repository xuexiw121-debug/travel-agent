import os
import requests
from typing import Optional, Dict, List, Tuple


class MapService:
    """高德地图服务"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GAODE_MAP_API_KEY", "")
        self.base_url = "https://restapi.amap.com/v3"

    def geocode(self, address: str, city: str = "") -> Optional[Dict[str, float]]:
        """
        地理编码 - 将地址转换为坐标

        参数:
            address: 地址
            city: 城市名

        返回:
            {"lat": float, "lng": float} 或 None
        """
        if not self.api_key:
            return None

        url = f"{self.base_url}/geocode/geo"
        params = {
            "key": self.api_key,
            "address": address,
            "city": city
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get("status") == "1" and data.get("geocodes"):
                location = data["geocodes"][0]["location"].split(",")
                return {
                    "lng": float(location[0]),
                    "lat": float(location[1])
                }
        except Exception as e:
            print(f"地理编码失败: {e}")

        return None

    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        逆地理编码 - 将坐标转换为地址

        参数:
            lat: 纬度
            lng: 经度

        返回:
            地址字符串或 None
        """
        if not self.api_key:
            return None

        url = f"{self.base_url}/geocode/regeo"
        params = {
            "key": self.api_key,
            "location": f"{lng},{lat}"
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get("status") == "1" and data.get("regeocode"):
                return data["regeocode"].get("formatted_address")
        except Exception as e:
            print(f"逆地理编码失败: {e}")

        return None

    def get_distance(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        mode: str = "driving"
    ) -> Optional[Dict]:
        """
        获取两点之间的距离和时间

        参数:
            origin: 起点坐标 {"lat":, "lng":}
            destination: 终点坐标 {"lat":, "lng":}
            mode: 出行方式 (driving, walking, cycling)

        返回:
            {"distance_km": float, "duration_min": int}
        """
        if not self.api_key:
            return None

        mode_map = {
            "driving": 1,
            "walking": 2,
            "cycling": 3
        }

        url = f"{self.base_url}/distance"
        params = {
            "key": self.api_key,
            "origins": f"{origin['lng']},{origin['lat']}",
            "destination": f"{destination['lng']},{destination['lat']}",
            "type": mode_map.get(mode, 1)
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get("status") == "1" and data.get("results"):
                result = data["results"][0]
                return {
                    "distance_km": int(result.get("distance", 0)) / 1000,
                    "duration_min": int(result.get("duration", 0)) // 60
                }
        except Exception as e:
            print(f"距离计算失败: {e}")

        return None

    def get_route(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        mode: str = "driving"
    ) -> Optional[List[Dict]]:
        """
        获取路线规划

        参数:
            origin: 起点坐标
            destination: 终点坐标
            mode: 出行方式

        返回:
            路线步骤列表
        """
        if not self.api_key:
            return None

        # driving: 驾车, walking: 步行, cycling: 骑行
        type_map = {
            "driving": "10",
            "walking": "20",
            "cycling": "30"
        }

        url = f"{self.base_url}/direction/{mode}"
        params = {
            "key": self.api_key,
            "origin": f"{origin['lng']},{origin['lat']}",
            "destination": f"{destination['lng']},{destination['lat']}"
        }

        # 驾车需要额外参数
        if mode == "driving":
            params["strategy"] = "0"  # 最速度优先

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get("status") == "1" and data.get("route"):
                paths = data["route"].get("paths", [])
                if paths:
                    steps = []
                    for step in paths[0].get("steps", []):
                        steps.append({
                            "instruction": step.get("instruction", ""),
                            "distance": int(step.get("distance", 0)),
                            "duration": int(step.get("duration", 0)) // 60
                        })
                    return steps
        except Exception as e:
            print(f"路线规划失败: {e}")

        return None

    def search_nearby(
        self,
        center: Dict[str, float],
        radius: int = 1000,
        types: str = ""
    ) -> List[Dict]:
        """
        附近搜索

        参数:
            center: 中心点坐标
            radius: 搜索半径(米)
            types: POI类型 (如 "风景名胜|餐饮")

        返回:
            POI列表
        """
        if not self.api_key:
            return []

        url = f"{self.base_url}/place/around"
        params = {
            "key": self.api_key,
            "location": f"{center['lng']},{center['lat']}",
            "radius": radius,
            "types": types
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get("status") == "1" and data.get("pois"):
                results = []
                for poi in data["pois"]:
                    location = poi.get("location", "").split(",")
                    if len(location) == 2:
                        results.append({
                            "name": poi.get("name", ""),
                            "address": poi.get("address", ""),
                            "type": poi.get("type", ""),
                            "location": {
                                "lng": float(location[0]),
                                "lat": float(location[1])
                            }
                        })
                return results
        except Exception as e:
            print(f"附近搜索失败: {e}")

        return []


# 全局单例
_map_service: Optional[MapService] = None


def get_map_service() -> MapService:
    """获取全局地图服务实例"""
    global _map_service
    if _map_service is None:
        _map_service = MapService()
    return _map_service
