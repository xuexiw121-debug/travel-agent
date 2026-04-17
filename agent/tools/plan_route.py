from typing import List, Dict, Tuple
from .calculate_distance import calculate_distance


def plan_route(
    attractions: List[Dict],
    start_point: str = "",
    end_point: str = "",
    optimize_for: str = "time"
) -> Dict:
    """
    规划最优路线

    参数:
        attractions: 景点列表，每个元素包含 coordinates: {"lat":, "lng":}
        start_point: 起始点坐标 {"lat":, "lng":}
        end_point: 终点坐标 {"lat":, "lng":}
        optimize_for: 优化目标 ("time", "distance")

    返回:
        {
            "route": [景点索引顺序],
            "total_distance_km": float,
            "total_duration_min": int,
            "daily_routes": [[每天的景点索引]]
        }
    """
    if not attractions:
        return {"error": "没有景点可供规划"}

    n = len(attractions)

    # 如果只有1-2个景点，直接返回原顺序
    if n <= 2:
        return _build_simple_route(attractions, start_point, end_point)

    # 使用贪心算法求解近似最优路线
    # 1. 计算所有景点之间的距离矩阵
    distance_matrix = _build_distance_matrix(attractions, start_point, end_point)

    # 2. 使用最近邻算法求解
    route = _nearest_neighbor_route(distance_matrix, n)

    # 3. 计算总距离和总时间
    total_distance, total_duration = _calculate_total_distance_time(
        route, distance_matrix, attractions, start_point, end_point
    )

    # 4. 分配每日行程 (每天不超过5个景点，不超过8小时)
    daily_routes = _distribute_to_days(route, attractions, start_point)

    return {
        "route": route,
        "total_distance_km": round(total_distance, 2),
        "total_duration_min": total_duration,
        "daily_routes": daily_routes,
        "attractions_order": [attractions[i]["name"] for i in route]
    }


def _build_simple_route(
    attractions: List[Dict],
    start_point: str,
    end_point: str
) -> Dict:
    """构建简单路线的返回结果"""
    route = list(range(len(attractions)))
    total_distance = 0
    total_duration = 0

    prev = start_point if start_point else None

    for a in attractions:
        if prev and "coordinates" in a:
            dist = calculate_distance(prev, a["coordinates"])
            total_distance += dist["distance_km"]
            total_duration += dist["duration_min"]
        prev = a.get("coordinates")

    if end_point and prev:
        dist = calculate_distance(prev, end_point)
        total_distance += dist["distance_km"]
        total_duration += dist["duration_min"]

    return {
        "route": route,
        "total_distance_km": round(total_distance, 2),
        "total_duration_min": total_duration,
        "daily_routes": [route],
        "attractions_order": [a["name"] for a in attractions]
    }


def _build_distance_matrix(
    attractions: List[Dict],
    start_point: str,
    end_point: str
) -> List[List[float]]:
    """构建距离矩阵"""
    n = len(attractions)
    matrix = [[0.0] * (n + 2) for _ in range(n + 2)]  # 包含起点和终点

    points = []
    if start_point:
        points.append(start_point)
    points.extend([a.get("coordinates", {}) for a in attractions])
    if end_point:
        points.append(end_point)

    # 计算所有点对之间的距离
    for i in range(len(points)):
        for j in range(len(points)):
            if i != j and points[i] and points[j]:
                dist = calculate_distance(points[i], points[j])
                matrix[i][j] = dist["distance_km"]

    return matrix


def _nearest_neighbor_route(distance_matrix: List[List[float]], n: int) -> List[int]:
    """最近邻算法求解TSP近似最优解"""
    if n == 0:
        return []

    # 从第一个景点开始
    visited = [False] * n
    route = []

    # 确定起始索引（考虑是否有起点）
    start_idx = 1 if distance_matrix[0][n + 1] > 0 else 0

    current = start_idx
    visited[current - 1] = True
    route.append(current - 1)

    for _ in range(n - 1):
        nearest = -1
        min_dist = float('inf')

        for j in range(n):
            if not visited[j] and matrix[current][j + 1] < min_dist:
                min_dist = matrix[current][j + 1]
                nearest = j

        if nearest >= 0:
            route.append(nearest)
            visited[nearest] = True
            current = nearest + 1

    return route


# 修复矩阵引用问题
def _nearest_neighbor_route(distance_matrix: List[List[float]], n: int) -> List[int]:
    """最近邻算法求解TSP近似最优解"""
    if n == 0:
        return []

    visited = [False] * n
    route = []

    # 确定起始索引（考虑是否有起点）
    start_idx = 1 if len(distance_matrix) > n + 1 else 0

    current = start_idx
    visited[current - 1 if current > 0 else 0] = True
    route.append(current - 1 if current > 0 else 0)

    for _ in range(n - 1):
        nearest = -1
        min_dist = float('inf')

        for j in range(n):
            if not visited[j]:
                # distance_matrix 的索引偏移
                matrix_i = current if current <= n else n + 1
                matrix_j = j + 1

                if matrix_i < len(distance_matrix) and matrix_j < len(distance_matrix[matrix_i]):
                    dist = distance_matrix[matrix_i][matrix_j]
                    if dist < min_dist:
                        min_dist = dist
                        nearest = j

        if nearest >= 0:
            route.append(nearest)
            visited[nearest] = True
            current = nearest + 1

    return route


def _calculate_total_distance_time(
    route: List[int],
    distance_matrix: List[List[float]],
    attractions: List[Dict],
    start_point: str,
    end_point: str
) -> Tuple[float, int]:
    """计算路线总距离和总时间"""
    total_distance = 0
    total_duration = 0

    # 从起点到第一个景点
    if start_point and "coordinates" in attractions[route[0]]:
        dist = calculate_distance(
            start_point,
            attractions[route[0]]["coordinates"]
        )
        total_distance += dist["distance_km"]
        total_duration += dist["duration_min"]

    # 景点之间
    for i in range(len(route) - 1):
        idx1, idx2 = route[i], route[i + 1]
        if "coordinates" in attractions[idx1] and "coordinates" in attractions[idx2]:
            dist = calculate_distance(
                attractions[idx1]["coordinates"],
                attractions[idx2]["coordinates"]
            )
            total_distance += dist["distance_km"]
            total_duration += dist["duration_min"]

    # 从最后一个景点到终点
    if end_point and "coordinates" in attractions[route[-1]]:
        dist = calculate_distance(
            attractions[route[-1]]["coordinates"],
            end_point
        )
        total_distance += dist["distance_km"]
        total_duration += dist["duration_min"]

    return total_distance, total_duration


def _distribute_to_days(route: List[int], attractions: List[Dict], start_point: str) -> List[List[int]]:
    """将路线分配到每天"""
    daily_routes = []
    current_day = []
    current_duration = 0
    max_duration_per_day = 8 * 60  # 8小时

    for idx in route:
        attraction = attractions[idx]
        visit_duration = _parse_duration(attraction.get("duration", "1小时"))

        if current_duration + visit_duration > max_duration_per_day and current_day:
            daily_routes.append(current_day)
            current_day = [idx]
            current_duration = visit_duration
        else:
            current_day.append(idx)
            current_duration += visit_duration

    if current_day:
        daily_routes.append(current_day)

    return daily_routes


def _parse_duration(duration_str: str) -> int:
    """解析游览时长字符串为分钟"""
    duration_str = duration_str.lower()

    if "天" in duration_str:
        try:
            return int(duration_str.replace("天", "").strip()) * 8 * 60
        except:
            return 8 * 60

    hours = 0
    if "小时" in duration_str:
        try:
            hours = int(duration_str.replace("小时", "").strip())
        except:
            hours = 1

    if "半" in duration_str:
        hours += 0.5

    return int(hours * 60)


if __name__ == "__main__":
    # 测试
    attractions = [
        {"name": "外滩", "coordinates": {"lat": 31.2405, "lng": 121.4901}, "duration": "2小时"},
        {"name": "东方明珠", "coordinates": {"lat": 31.2397, "lng": 121.4998}, "duration": "3小时"},
        {"name": "豫园", "coordinates": {"lat": 31.2277, "lng": 121.4899}, "duration": "2小时"},
    ]

    result = plan_route(attractions)
    print(f"路线: {result['attractions_order']}")
    print(f"总距离: {result['total_distance_km']} km")
    print(f"总时间: {result['total_duration_min']} 分钟")
    print(f"每日路线: {result['daily_routes']}")
