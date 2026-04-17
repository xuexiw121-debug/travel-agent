from langchain.agents import tool
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage


def create_memory() -> ConversationBufferMemory:
    """创建对话记忆"""
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )
    return memory


def add_to_memory(memory: ConversationBufferMemory, user_input: str, agent_response: str):
    """向记忆中添加对话"""
    memory.chat_memory.add_user_message(user_input)
    memory.chat_memory.add_ai_message(agent_response)


def get_memory_context(memory: ConversationBufferMemory) -> str:
    """获取记忆中的上下文"""
    messages = memory.chat_memory.messages
    if not messages:
        return ""

    context = "以下是之前的对话历史:\n"
    for msg in messages[-6:]:  # 只保留最近6条消息
        if isinstance(msg, HumanMessage):
            context += f"用户: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            context += f"助手: {msg.content}\n"
    return context
