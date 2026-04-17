import os
import re
import json
from typing import Optional, Dict, List
from langchain.agents import AgentExecutor, create_react_agent, tool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage

from .prompts.travel_prompt import TRAVEL_AGENT_PROMPT
from .tools.search_attractions import search_attractions
from .tools.calculate_distance import calculate_distance
from .tools.plan_route import plan_route
from .memory.conversation_memory import create_memory, add_to_memory, get_memory_context


def get_minimax_llm():
    """获取 MiniMax LLM 实例"""
    try:
        from langchain.chat_models import ChatMinimax
        minimax_api_key = os.getenv("MINIMAX_API_KEY", "")
        if not minimax_api_key:
            return None
        return ChatMinimax(
            model="MiniMax-Text-01",
            minimax_api_key=minimax_api_key,
            temperature=0.7
        )
    except ImportError:
        return None


def create_travel_agent():
    """创建旅游规划 Agent"""

    # 初始化 MiniMax LLM
    llm = get_minimax_llm()

    # 定义工具
    @tool
    def search_attractions_tool(destination: str, category: Optional[str] = None, keywords: Optional[str] = None) -> str:
        """
        搜索景点信息。

        参数:
            destination: 目的地城市名称
            category: 景点类别 (natural, cultural, theme_park, food, shopping)
            keywords: 关键词，多个关键词用逗号分隔

        返回:
            景点列表的JSON字符串
        """
        keyword_list = keywords.split(",") if keywords else None
        results = search_attractions(destination, category, keyword_list)
        return str(results)

    @tool
    def calculate_distance_tool(
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> str:
        """
        计算两个地点之间的距离。

        参数:
            lat1: 第一个地点的纬度
            lng1: 第一个地点的经度
            lat2: 第二个地点的纬度
            lng2: 第二个地点的经度

        返回:
            距离和预计时间的JSON字符串
        """
        point1 = {"lat": lat1, "lng": lng1}
        point2 = {"lat": lat2, "lng": lng2}
        result = calculate_distance(point1, point2)
        return str(result)

    @tool
    def plan_route_tool(
        attractions_json: str,
        start_lat: Optional[float] = None,
        start_lng: Optional[float] = None,
        end_lat: Optional[float] = None,
        end_lng: Optional[float] = None
    ) -> str:
        """
        规划最优游览路线。

        参数:
            attractions_json: 景点列表的JSON字符串
            start_lat, start_lng: 起始点坐标（可选）
            end_lat, end_lng: 终点坐标（可选）

        返回:
            路线规划的JSON字符串
        """
        import json
        attractions = json.loads(attractions_json)

        start_point = {"lat": start_lat, "lng": start_lng} if start_lat and start_lng else None
        end_point = {"lat": end_lat, "lng": end_lng} if end_lat and end_lng else None

        result = plan_route(attractions, start_point, end_point)
        return str(result)

    @tool
    def generate_itinerary_tool(
        route_json: str,
        days: int,
        people: int = 1
    ) -> str:
        """
        生成详细行程安排。

        参数:
            route_json: 路线规划结果的JSON字符串
            days: 旅行天数
            people: 人数

        返回:
            详细行程安排的字符串
        """
        import json
        import json

        route_data = json.loads(route_json)
        daily_routes = route_data.get("daily_routes", [])

        itinerary = f"# {days}天{people}人旅行行程安排\n\n"

        for day_idx, day_route in enumerate(daily_routes, 1):
            itinerary += f"## 第{day_idx}天\n\n"

            for i, attr_idx in enumerate(day_route):
                if attr_idx < len(route_data.get("attractions_order", [])):
                    attr_name = route_data["attractions_order"][attr_idx]
                    itinerary += f"- {attr_name}\n"

            itinerary += "\n"

        return itinerary

    # 工具列表
    tools = [
        search_attractions_tool,
        calculate_distance_tool,
        plan_route_tool,
        generate_itinerary_tool
    ]

    # 创建 ReAct Agent
    prompt = PromptTemplate.from_template("""
你是一个专业的旅游规划助手。

历史对话:
{chat_history}

用户问题: {input}
{agent_scratchpad}
""")

    agent = create_react_agent(llm, tools, prompt)

    # 创建 Agent Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=create_memory(),
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True
    )

    return agent_executor


class TravelAgent:
    """旅游规划 Agent 封装类"""

    def __init__(self):
        self._agent = None
        self._memory = create_memory()

    @property
    def agent(self):
        if self._agent is None:
            self._agent = create_travel_agent()
        return self._agent

    def plan_trip(
        self,
        destination: str,
        days: int,
        people: int = 1,
        preferences: str = ""
    ) -> str:
        """
        规划旅行

        参数:
            destination: 目的地
            days: 天数
            people: 人数
            preferences: 偏好描述

        返回:
            生成的行程安排
        """
        user_input = f"我想去{destination}旅行，{days}天，{people}人。"

        if preferences:
            user_input += f"偏好: {preferences}"

        # 获取记忆上下文
        memory_context = get_memory_context(self._memory)

        # 调用 Agent
        result = self.agent.invoke({
            "input": user_input,
            "chat_history": memory_context
        })

        # 保存到记忆
        add_to_memory(self._memory, user_input, result["output"])

        return result["output"]

    def chat(self, message: str) -> str:
        """
        与 Agent 对话

        参数:
            message: 用户消息

        返回:
            Agent 回复
        """
        memory_context = get_memory_context(self._memory)

        result = self.agent.invoke({
            "input": message,
            "chat_history": memory_context
        })

        add_to_memory(self._memory, message, result["output"])

        return result["output"]

    def reset_memory(self):
        """重置对话记忆"""
        self._memory = create_memory()
        if self._agent:
            self._agent.memory = self._memory


# 全局单例
_travel_agent: Optional[TravelAgent] = None


def get_travel_agent() -> TravelAgent:
    """获取全局旅游 Agent 实例"""
    global _travel_agent
    if _travel_agent is None:
        _travel_agent = TravelAgent()
    return _travel_agent


if __name__ == "__main__":
    # 测试
    agent = get_travel_agent()
    result = agent.plan_trip("上海", 3, 2, "亲子")
    print(result)
