"""
LLM 内容生成服务 - 使用 MiniMax 生成更详细的行程描述
"""

import os
import json
from typing import Dict, List, Optional


def _extract_minimax_text(result: Dict) -> Optional[str]:
    """从 MiniMax 响应中提取文本内容，兼容多种返回格式。"""
    if not result or not isinstance(result, dict):
        return None

    reply = result.get("reply")
    if reply:
        return reply

    choices = result.get("choices")
    if not choices or not isinstance(choices, list):
        return None

    choice = choices[0]
    if not isinstance(choice, dict):
        return None

    message = choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if content:
            return content

    messages = choice.get("messages")
    if isinstance(messages, list) and messages:
        first_msg = messages[0]
        if isinstance(first_msg, dict):
            content = first_msg.get("content") or first_msg.get("text")
            if content:
                return content

    text = choice.get("text") or choice.get("content")
    if text:
        return text

    return None


def _get_minimax_bot_setting() -> List[Dict]:
    """获取 MiniMax bot_setting，支持通过环境变量注入。"""
    raw = os.getenv("MINIMAX_BOT_SETTING_JSON", "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
        except Exception:
            pass

    return [
        {
            "bot_name": "TravelPlanner",
            "content": "你是一个专业的旅游规划助手，擅长生成清晰、实用的行程建议。"
        }
    ]


def _get_minimax_reply_constraints(max_tokens: int) -> Dict:
    """构建 MiniMax reply_constraints（必填）。"""
    return {
        "sender_type": "BOT",
        "sender_name": "TravelPlanner",
        "max_tokens": max_tokens
    }


def _get_minimax_parameters(max_tokens: int, temperature: float) -> Dict:
    """补充 MiniMax parameters，兼容不同字段约定。"""
    return {
        "max_tokens": max_tokens,
        "temperature": temperature
    }


def generate_detailed_itinerary_with_llm(
    destination: str,
    days: int,
    people: int,
    preferences: List[str],
    attractions: List[Dict],
    daily_routes: List[List[int]]
) -> str:
    """
    使用 LLM 生成详细的行程描述

    参数:
        destination: 目的地
        days: 天数
        people: 人数
        preferences: 偏好列表
        attractions: 景点列表
        daily_routes: 每日路线

    返回:
        LLM 生成的详细行程描述
    """
    minimax_key = os.getenv("MINIMAX_API_KEY", "sk-api-wdm2GZuumZ7CmvoOZ89OH5EwPoG4UR8MJtQRdBBZWeTd11EKr1aARsSgTFYOoxHu-BOgTFRwuQ-hDR9W4jczQ_8-57v9I_GesbJtmhFhyYJKXCRrTyJxT98")
    if not minimax_key:
        return _generate_fallback_text(destination, days, people, preferences, attractions, daily_routes)

    try:
        import requests

        # 构建景点信息摘要
        attraction_details = []
        for a in attractions[:8]:  # 最多8个景点
            detail = f"- {a.get('name', '')}: {a.get('description', '')} (建议游览{a.get('duration', '1-2小时')}, 门票{a.get('ticket', '未知')})"
            attraction_details.append(detail)

        prompt = f"""请为以下旅行计划生成一段详细、富有吸引力的中文行程描述：

目的地：{destination}
天数：{days}天
人数：{people}人
偏好：{', '.join(preferences) if preferences else '综合游'}

精选景点：
{chr(10).join(attraction_details)}

请生成一段优美、详细、实用的行程描述，包括：
1. 欢迎语和行程亮点
2. 每一天的游览主题和推荐理由
3. 每个景点的特色介绍和拍照点推荐
4. 当地美食推荐
5. 实用的旅行小贴士

要求语言生动、有感染力，字数300-500字。"""

        response = requests.post(
            "https://api.minimax.chat/v1/text/chatcompletion_pro",
            headers={
                "Authorization": f"Bearer {minimax_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "MiniMax-Text-01",
                "messages": [
                    {
                        "sender_type": "USER",
                        "sender_name": "User",
                        "text": prompt
                    }
                ],
                "bot_setting": _get_minimax_bot_setting(),
                "reply_constraints": _get_minimax_reply_constraints(1200),
                "parameters": _get_minimax_parameters(1200, 0.7),
                "temperature": 0.7,
                "max_tokens": 1200,
                "tokens_to_generate": 1200
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if os.getenv("MINIMAX_DEBUG", ""):
                print(f"MiniMax raw response: {result}")
            extracted = _extract_minimax_text(result)
            if extracted:
                return extracted
        # 如果任何一步失败，使用 fallback
        return _generate_fallback_text(destination, days, people, preferences, attractions, daily_routes)

    except Exception as e:
        print(f"LLM 调用失败: {e}")
        return _generate_fallback_text(destination, days, people, preferences, attractions, daily_routes)


def _generate_fallback_text(
    destination: str,
    days: int,
    people: int,
    preferences: List[str],
    attractions: List[Dict],
    daily_routes: List[List[int]]
) -> str:
    """生成基础行程描述（无 LLM 时使用）"""

    lines = []
    lines.append(f"# 🏝️ {destination} {days}天{people}人精品游")
    lines.append("")
    lines.append(f"**旅行类型**: {', '.join(preferences) if preferences else '综合游'}")
    lines.append("")

    # 景点按天分组
    attractions_by_name = {a.get("name"): a for a in attractions}

    for day_idx, route in enumerate(daily_routes, 1):
        lines.append(f"## 📅 第{day_idx}天")

        morning_attractions = route[:2] if len(route) >= 2 else route
        afternoon_attractions = route[2:] if len(route) > 2 else []

        # 上午
        lines.append("### ☀️ 上午")
        for attr_idx in morning_attractions:
            if attr_idx < len(attractions):
                attr = attractions[attr_idx]
                lines.append(f"**{attr.get('name', '未知景点')}**")
                lines.append(f"   📍 {attr.get('description', '')}")
                lines.append(f"   ⏱️ 建议游览: {attr.get('duration', '1-2小时')}")
                lines.append(f"   🎟️ 门票: {attr.get('ticket', '未知')}")
                lines.append(f"   📷 拍照点: {attr.get('best_time', '任意时间')} 最佳")
                if attr.get('tags'):
                    lines.append(f"   🏷️ 标签: {', '.join(attr.get('tags', []))}")
                lines.append("")

        # 午餐
        lines.append("### 🍜 午餐推荐")
        lines.append("   品尝当地特色美食，推荐尝试：")
        lines.append("   - 本地小吃一条街")
        lines.append("   - 特色农家菜")
        lines.append("   - 景区周边餐厅")
        lines.append("")

        # 下午
        if afternoon_attractions:
            lines.append("### 🌤️ 下午")
            for attr_idx in afternoon_attractions:
                if attr_idx < len(attractions):
                    attr = attractions[attr_idx]
                    lines.append(f"**{attr.get('name', '未知景点')}**")
                    lines.append(f"   📍 {attr.get('description', '')}")
                    lines.append(f"   ⏱️ 建议游览: {attr.get('duration', '1-2小时')}")
                    lines.append("")

        # 晚餐
        lines.append("### 🍽️ 晚餐推荐")
        lines.append("   体验当地夜生活，推荐：")
        lines.append("   - 江景餐厅（如果有水系）")
        lines.append("   - 当地网红餐厅")
        lines.append("   - 夜市美食街")
        lines.append("")

        # 小贴士
        lines.append("### 💡 今日小贴士")
        tips = [
            "早点出发，避开人流高峰",
            "穿着舒适的步行鞋",
            "随身携带充电宝",
            "注意防晒或防雨"
        ]
        for tip in tips:
            lines.append(f"- {tip}")
        lines.append("")

        lines.append("---")
        lines.append("")

    # 总结
    lines.append("# 📊 行程总结")
    lines.append("")
    lines.append(f"| 项目 | 详情 |")
    lines.append("|------|------|")
    lines.append(f"| 目的地 | {destination} |")
    lines.append(f"| 天数 | {days}天 |")
    lines.append(f"| 人数 | {people}人 |")
    lines.append(f"| 景点数量 | {len(attractions)}个 |")
    if preferences:
        lines.append(f"| 旅行类型 | {', '.join(preferences)} |")
    lines.append("")
    lines.append("**⚠️ 注意事项**: ")
    lines.append("- 门票价格仅供参考，以景区官方为准")
    lines.append("- 建议提前查看天气预报")
    lines.append("- 热门景点建议提前预约")

    return "\n".join(lines)


def generate_attraction_description(attr: Dict) -> str:
    """为单个景点生成详细描述"""
    lines = []
    lines.append(f"## 🏛️ {attr.get('name', '未知景点')}")
    lines.append("")
    lines.append(f"**评分**: ⭐ {attr.get('rating', 0)}")
    lines.append(f"**门票**: {attr.get('ticket', '未知')}")
    lines.append(f"**游览时长**: {attr.get('duration', '1-2小时')}")
    lines.append(f"**最佳游览时间**: {attr.get('best_time', '任意时间')}")
    lines.append("")
    lines.append(f"### 📝 景点介绍")
    lines.append(attr.get('description', '暂无描述'))
    lines.append("")
    lines.append(f"### 🏷️ 特色标签")
    tags = attr.get('tags', [])
    if tags:
        lines.append(", ".join([f"`{t}`" for t in tags]))
    lines.append("")
    lines.append(f"### 📍 实用信息")
    lines.append(f"- 开放时间: {attr.get('hours', '未知')}")
    lines.append(f"- 适合人群: {', '.join(attr.get('suitable_for', ['所有人群']))}")

    if attr.get('coordinates'):
        lines.append(f"- 坐标: {attr['coordinates'].get('lat', '')}, {attr['coordinates'].get('lng', '')}")

    return "\n".join(lines)


def chat_with_llm(user_message: str, itinerary_context: str = "") -> str:
    """
    使用 LLM 进行对话

    参数:
        user_message: 用户输入的消息
        itinerary_context: 行程上下文

    返回:
        LLM 生成的回复
    """
    minimax_key = os.getenv("MINIMAX_API_KEY", "")
    if not minimax_key:
        return _get_fallback_chat_response(user_message, itinerary_context)

    try:
        import requests

        # 构建上下文提示
        context_prompt = ""
        if itinerary_context:
            context_prompt = f"\n\n当前行程信息：\n{itinerary_context}\n"

        prompt = f"""你是一个热情、专业的旅游规划助手。用户正在规划旅行，请用友好、生动的方式回答他们的问题。

{context_prompt}

用户问题：{user_message}

请用中文回答，语言生动有感染力，像和朋友聊天一样。如果涉及具体景点、美食、交通等，要给出实用、有价值的建议。字数控制在100-200字。"""

        response = requests.post(
            "https://api.minimax.chat/v1/text/chatcompletion_pro",
            headers={
                "Authorization": f"Bearer {minimax_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "MiniMax-Text-01",
                "messages": [
                    {
                        "sender_type": "USER",
                        "sender_name": "User",
                        "text": prompt
                    }
                ],
                "bot_setting": _get_minimax_bot_setting(),
                "reply_constraints": _get_minimax_reply_constraints(600),
                "parameters": _get_minimax_parameters(600, 0.8),
                "temperature": 0.8,
                "max_tokens": 600,
                "tokens_to_generate": 600
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if os.getenv("MINIMAX_DEBUG", ""):
                print(f"MiniMax raw response: {result}")
            extracted = _extract_minimax_text(result)
            if extracted:
                return extracted

        return _get_fallback_chat_response(user_message, itinerary_context)

    except Exception as e:
        print(f"LLM 聊天调用失败: {e}")
        return _get_fallback_chat_response(user_message, itinerary_context)


def _get_fallback_chat_response(user_message: str, itinerary_context: str) -> str:
    """无 LLM 时的回退回复"""
    msg_lower = user_message.lower()

    if any(k in msg_lower for k in ["调整", "修改", "换", "改变"]):
        return """好的，请告诉我您想如何调整行程？例如：

• 增加或减少景点
• 调整每天的行程节奏（轻松一点/紧凑一点）
• 侧重特定类型的景点（自然风光/人文历史/亲子乐园）
• 调整预算
• 更换某个具体的景点

直接告诉我您的想法，我会帮您重新规划！"""

    elif any(k in msg_lower for k in ["推荐", "美食", "好吃", "餐厅", "吃什么"]):
        if itinerary_context:
            return """当地美食推荐建议：

• 先问问酒店前台或民宿老板，他们通常知道最地道的本地餐馆
• 搜索当地的"美食街"或"夜市"，一般都能找到特色小吃
• 打开大众点评或小红书，搜索目的地+美食，看看当地人推荐什么
• 尝试当地早餐、路边摊，这是最有烟火气的美食体验

要不要我根据您的目的地，给您推荐一些具体的餐厅？"""
        return "请问您想去哪个城市呢？这样我可以给您更精准的美食推荐！"

    elif any(k in msg_lower for k in ["交通", "怎么去", "地铁", "公交", "打车"]):
        return """交通建议：

• **地铁**：城市内最方便快捷的交通方式，下载"Metro大都会"或当地地铁APP
• **公交**：票价便宜，覆盖面广，用百度地图/高德地图查路线很方便
• **打车/滴滴**：多人出行很划算，注意高峰期可能堵车
• **共享单车**：短距离骑行很方便，支付宝/微信直接扫码

建议提前在手机装好地图APP离线地图，以防信号不好。"""

    elif any(k in msg_lower for k in ["门票", "多少钱", "票", "价格", "费用"]):
        return """门票价格参考：

• **人文景点**（故宫、兵马俑等）：40-150元
• **自然风光**（西湖、漓江等）：20-200元
• **主题乐园**（迪士尼、欢乐谷等）：200-500元
• **博物馆**：大部分免费，部分特展需购票

**省钱建议**：
1. 提前在官方公众号/旅游平台购票，常有优惠
2. 关注"景区年卡"，多次游玩更划算
3. 学生证、老年证、军官证等可能有折扣"""

    elif any(k in msg_lower for k in ["注意", "tips", "建议", "小贴士", "提醒"]):
        return """旅行小贴士：

1. **提前查看天气预报**，带好防晒或雨具
2. **穿舒适的步行鞋**，每天走路很多
3. **带好身份证**，很多景点需刷证入园
4. **充电宝必备**，导航、拍照很耗电
5. **提前预约热门景点**，避免排队
6. **买一份旅游意外险**，出行更安心

还有什么想了解的？"""

    elif any(k in msg_lower for k in ["几月", "什么时候", "季节", "天气"]):
        return """最佳旅行时间建议：

• **春天（3-5月）**：花开时节，适合赏花、踏青
• **夏天（6-8月）**：避暑胜地人多，需要注意防晒防雨
• **秋天（9-11月）**：秋高气爽，是旅行的黄金季节
• **冬天（12-2月）**：看雪、泡温泉的好时候

不同目的地最佳时间不同，请告诉我您想去哪里，我给您具体建议！"""

    else:
        return f"""关于您的旅行，我可以帮您：

• 详细解释每个景点的特色和游览建议
• 调整或重新规划行程安排
• 推荐当地美食和餐厅
• 提供交通和门票方面的建议
• 分享实用的旅行小贴士

请告诉我您具体想了解什么？😊"""
