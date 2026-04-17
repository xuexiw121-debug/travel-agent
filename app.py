"""
旅游路线规划智能体 - Streamlit 应用
"""

import streamlit as st
import os
import sys
from dotenv import load_dotenv

load_dotenv()


# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.services.itinerary_service import get_itinerary_service
from agent.services.llm_service import generate_detailed_itinerary_with_llm, chat_with_llm

# 页面配置
st.set_page_config(
    page_title="旅游路线规划智能体",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .day-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1E88E5;
    }
    .attraction-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #eee;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
    }
    .info-box {
        background-color: #E3F2FD;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "itinerary" not in st.session_state:
        st.session_state.itinerary = None
    if "destination" not in st.session_state:
        st.session_state.destination = ""
    if "days" not in st.session_state:
        st.session_state.days = 3
    if "detailed_itinerary" not in st.session_state:
        st.session_state.detailed_itinerary = None
    if "detailed_itinerary_key" not in st.session_state:
        st.session_state.detailed_itinerary_key = ""


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("## 🗺️ 旅行设置")

        destination = st.text_input(
            "目的地",
            value=st.session_state.destination,
            placeholder="例如：上海、北京、成都",
            help="输入你想要去的城市"
        )

        days = st.slider(
            "旅行天数",
            min_value=1,
            max_value=7,
            value=st.session_state.days,
            help="选择旅行天数"
        )

        people = st.number_input(
            "人数",
            min_value=1,
            max_value=20,
            value=2,
            help="旅行人数"
        )

        preferences = st.multiselect(
            "偏好类型",
            options=["亲子", "情侣", "独自", "朋友", "老人", "摄影", "美食", "历史", "自然", "购物"],
            default=["亲子"],
            help="选择你感兴趣的景点类型"
        )

        st.markdown("---")

        if st.button("🎯 开始规划", type="primary", use_container_width=True):
            if destination:
                st.session_state.destination = destination
                st.session_state.days = days
                with st.spinner("正在规划您的旅行..."):
                    try:
                        itinerary_service = get_itinerary_service()
                        itinerary = itinerary_service.generate_itinerary(
                            destination=destination,
                            days=days,
                            people=people,
                            preferences=",".join(preferences)
                        )
                        if itinerary.get("error"):
                            st.error(itinerary["error"])
                        else:
                            st.session_state.itinerary = itinerary
                            st.session_state.messages = []
                            st.session_state.detailed_itinerary = None
                            st.session_state.detailed_itinerary_key = ""

                            # 添加欢迎消息
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"您好！我为您规划了 {destination} {days}天 {people}人 的旅行方案，请查看下方行程安排。您也可以随时问我问题来调整行程。"
                            })

                            st.rerun()
                    except Exception as e:
                        st.error(f"规划失败: {str(e)}")
            else:
                st.warning("请输入目的地")

        st.markdown("---")
        st.markdown("### 💡 使用提示")
        st.markdown("""
        1. 设置您的目的地和偏好
        2. 点击开始规划生成行程
        3. 查看生成的行程安排
        4. 可以继续对话调整行程
        """)

        st.markdown("---")
        st.markdown("### ⚙️ 设置")
        if st.button("🔄 重置对话"):
            st.session_state.messages = []
            st.session_state.itinerary = None
            st.rerun()

        # API Key 状态
        st.markdown("---")
        minimax_key = os.getenv("MINIMAX_API_KEY", "")
        if minimax_key:
            st.success("✅ MiniMax API 已配置")
        else:
            st.warning("⚠️ 请设置 MINIMAX_API_KEY 环境变量")

        return destination, days, people, preferences


def render_chat():
    """渲染聊天界面"""
    st.markdown("## 💬 与智能体对话")

    # 显示聊天历史
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 聊天输入
    if prompt := st.chat_input("输入您的问题或要求..."):
        # 添加用户消息
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        with st.chat_message("user"):
            st.markdown(prompt)

        # 生成回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    response = generate_response(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                except Exception as e:
                    st.error(f"生成回复失败: {str(e)}")


def generate_response(prompt: str) -> str:
    """生成智能体回复 - 使用 LLM"""
    # 构建行程上下文
    itinerary = st.session_state.get("itinerary")
    itinerary_context = ""
    if itinerary:
        attractions = itinerary.get('attractions', [])
        attraction_names = [a.get('name', '') for a in attractions]
        itinerary_context = f"""目的地: {itinerary.get('destination', '')}
天数: {itinerary.get('days', 0)}天
人数: {itinerary.get('people', 0)}人
推荐景点: {', '.join(attraction_names[:5])}..."""

    # 调用 LLM 生成回复
    return chat_with_llm(prompt, itinerary_context)


def render_itinerary():
    """渲染行程展示"""
    itinerary = st.session_state.get("itinerary")

    if not itinerary:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background-color: #f5f5f5; border-radius: 10px;">
            <h2 style="color: #666;">🎒 还没有规划行程</h2>
            <p style="color: #999;">请在侧边栏设置目的地和偏好，然后点击"开始规划"</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if itinerary.get("error"):
        st.error(itinerary["error"])
        return

    # 使用 LLM 生成更详细的行程描述（仅在行程变化时生成）
    detail_key = f"{itinerary.get('destination','')}|{itinerary.get('days',0)}|{itinerary.get('people',0)}|{itinerary.get('preferences','')}|{len(itinerary.get('attractions', []))}"
    if st.session_state.detailed_itinerary_key != detail_key:
        with st.spinner("正在生成详细行程描述..."):
            try:
                preferences_list = itinerary.get('preferences', '').split(',') if itinerary.get('preferences') else []
                attractions = itinerary.get('attractions', [])
                name_to_index = {a.get('name', ''): idx for idx, a in enumerate(attractions)}
                daily_routes = []
                for day in itinerary.get('daily_itineraries', []):
                    day_indices = [name_to_index.get(name) for name in day.get('attractions', [])]
                    daily_routes.append([idx for idx in day_indices if idx is not None])

                detailed_text = generate_detailed_itinerary_with_llm(
                    destination=itinerary.get('destination', ''),
                    days=itinerary.get('days', 3),
                    people=itinerary.get('people', 2),
                    preferences=preferences_list,
                    attractions=attractions,
                    daily_routes=daily_routes
                )
                st.session_state.detailed_itinerary = detailed_text
                st.session_state.detailed_itinerary_key = detail_key
            except Exception:
                st.session_state.detailed_itinerary = None

    # 行程概览
    st.markdown("---")
    st.markdown(f"## 📍 {itinerary['destination']} {itinerary['days']}天 {itinerary['people']}人 旅行方案")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("旅行天数", f"{itinerary['days']}天")
    with col2:
        st.metric("预计总距离", f"约 {itinerary.get('total_distance_km', 0)} 公里")
    with col3:
        st.metric("推荐景点", f"{len(itinerary.get('attractions', []))} 个")

    # 显示 LLM 生成的详细行程
    detailed = st.session_state.get("detailed_itinerary")
    if detailed:
        with st.expander("📖 查看 LLM 生成的详细行程描述", expanded=True):
            st.markdown(detailed)

    # 每日行程详情
    st.markdown("---")
    st.markdown("### 📅 每日行程详情")

    tabs = st.tabs([f"第{i['day']}天" for i in itinerary.get('daily_itineraries', [])])

    for idx, (tab, day_info) in enumerate(zip(tabs, itinerary.get('daily_itineraries', []))):
        with tab:
            st.markdown(f"**主题**: {day_info.get('theme', '')}")

            # 早餐
            breakfast = day_info.get('breakfast', {})
            with st.expander("🍳 早餐推荐", expanded=False):
                st.write(f"**推荐**: {breakfast.get('suggestion', '')}")
                st.write(f"⏰ 时间: {breakfast.get('time', '')}")
                st.write(f"💰 预算: {breakfast.get('budget', '')}")

            # 景点
            attractions = day_info.get('attractions', [])
            if attractions:
                st.markdown("#### 🏛️ 推荐景点")
                for attr in attractions:
                    st.markdown(f"- **{attr}**")

            # 午餐
            lunch = day_info.get('lunch', {})
            with st.expander("🍜 午餐推荐", expanded=False):
                st.write(f"**推荐**: {lunch.get('suggestion', '')}")
                st.write(f"⏰ 时间: {lunch.get('time', '')}")
                st.write(f"💰 预算: {lunch.get('budget', '')}")

            # 晚餐
            dinner = day_info.get('dinner', {})
            with st.expander("🍽️ 晚餐推荐", expanded=False):
                st.write(f"**推荐**: {dinner.get('suggestion', '')}")
                st.write(f"⏰ 时间: {dinner.get('time', '')}")
                st.write(f"💰 预算: {dinner.get('budget', '')}")

            # 小贴士
            tips = day_info.get('tips', [])
            if tips:
                with st.expander("💡 温馨提示", expanded=False):
                    for tip in tips:
                        st.write(f"- {tip}")

    # 景点列表
    st.markdown("---")
    st.markdown("### 🗺️ 精选景点一览")

    attractions = itinerary.get('attractions', [])
    if attractions:
        cols = st.columns(2)
        for idx, attr in enumerate(attractions):
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"""
                    <div class="info-box">
                        <h4>{attr.get('name', '')}</h4>
                        <p><strong>评分</strong>: ⭐ {attr.get('rating', 0)} | <strong>门票</strong>: {attr.get('ticket', '')}</p>
                        <p>{attr.get('description', '')}</p>
                        <p><strong>建议游览</strong>: {attr.get('duration', '')} | <strong>最佳时间</strong>: {attr.get('best_time', '')}</p>
                        <p><strong>标签</strong>: {', '.join(attr.get('tags', []))}</p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("暂无景点数据")


def main():
    """主函数"""
    init_session_state()

    # 页面标题
    st.markdown('<h1 class="main-header">✈️ 旅游路线规划智能体</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">智能规划您的完美旅程</p>', unsafe_allow_html=True)

    # 渲染侧边栏
    destination, days, people, preferences = render_sidebar()

    # 主内容区
    col_main, col_chat = st.columns([2, 1])

    with col_main:
        render_itinerary()

    with col_chat:
        render_chat()


if __name__ == "__main__":
    main()
