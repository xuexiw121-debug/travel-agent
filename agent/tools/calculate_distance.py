import math
from typing import Dict, Tuple, Optional
import os
import requests

# 高德地图 API Key (建议通过环境变量配置)
GAODE_API_KEY = os.getenv("GAODE_MAP_API_KEY", "")


def calculate_distance(
    point1: Dict[str, float],
    point2: Dict[str, float],
    mode: str = "driving"
) -> Dict:
    """
    计算两个地点之间的距离和预计时间

    参数:
        point1: 第一个点 {"lat": float, "lng": float}
        point2: 第二个点 {"lat": float, "lng": float}
        mode: 出行方式 ("driving", "walking", "cycling")

    返回:
        {"distance_km": float, "duration_min": int, "route": str}
    """
    # 如果有高德API Key，使用真实API
    if GAODE_API_KEY:
        return _calculate_distance_api(point1, point2, mode)

    # 否则使用 Haversine 公式估算
    return _calculate_distance_haversine(point1, point2)


def _calculate_distance_haversine(
    point1: Dict[str, float],
    point2: Dict[str, float]
) -> Dict:
    """使用 Haversine 公式计算球面距离"""
    R = 6371  # 地球半径 (km)

    lat1, lng1 = math.radians(point1["lat"]), math.radians(point1["lng"])
    lat2, lng2 = math.radians(point2["lat"]), math.radians(point2["lng"])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))

    distance_km = R * c

    # 估算行车时间 (假设平均速度 30km/h)
    duration_min = int(distance_km / 30 * 60)

    return {
        "distance_km": round(distance_km, 2),
        "duration_min": duration_min,
        "route": f"直线距离约 {distance_km:.1f} 公里"
    }


def _calculate_distance_api(
    point1: Dict[str, float],
    point2: Dict[str, float],
    mode: str
) -> Dict:
    """使用高德地图 API 计算距离"""
    mode_map = {
        "driving": 1,
        "walking": 2,
        "cycling": 3
    }

    url = "https://restapi.amap.com/v3/distance"
    params = {
        "key": GAODE_API_KEY,
        "origins": f"{point1['lng']},{point1['lat']}",
        "destination": f"{point2['lng']},{point2['lat']}",
        "type": mode_map.get(mode, 1)
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get("status") == "1" and data.get("results"):
            result = data["results"][0]
            distance = int(result.get("distance", 0)) / 1000  # 转换为公里
            duration = int(result.get("duration", 0)) // 60  # 转换为分钟

            return {
                "distance_km": round(distance, 2),
                "duration_min": duration,
                "route": f"路线距离 {distance:.1f} 公里"
            }
    except Exception as e:
        print(f"高德API调用失败: {e}")

    # API失败时回退到Haversine
    return _calculate_distance_haversine(point1, point2)


def calculate_distance_by_address(
    address1: str,
    address2: str,
    city: str = ""
) -> Dict:
    """
    通过地址计算两个地点之间的距离

    参数:
        address1: 第一个地址
        address2: 第二个地址
        city: 城市名称（用于辅助地理编码）

    返回:
        {"distance_km": float, "duration_min": int}
    """
    # 地理编码
    coord1 = geocode_address(address1, city)
    coord2 = geocode_address(address2, city)

    if not coord1 or not coord2:
        return {"error": "无法解析地址"}

    return calculate_distance(coord1, coord2)


def geocode_address(address: str, city: str = "") -> Optional[Dict[str, float]]:
    """
    使用高德地图 API 进行地理编码

    参数:
        address: 地址
        city: 城市名

    返回:
        {"lat": float, "lng": float} 或 None
    """
    if not GAODE_API_KEY:
        return None

    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": GAODE_API_KEY,
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


if __name__ == "__main__":
    # 测试
    result = calculate_distance(
        {"lat": 31.2405, "lng": 121.4901},  # 外滩
        {"lat": 31.2397, "lng": 121.4998}   # 东方明珠
    )
    print(f"距离: {result['distance_km']} km, 时间: {result['duration_min']} 分钟")
