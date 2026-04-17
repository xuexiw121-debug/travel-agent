# 旅游路线规划智能体

核心版：根据用户选择生成行程，并在右侧提供聊天调整入口。

## 功能特性

- 景点推荐：根据目的地和偏好推荐热门景点
- 路线规划：生成分日行程安排
- 对话交互：右侧聊天用于调整与提问

## 技术栈

- **前端**: Streamlit (Python Web 框架)
- **LLM (可选)**: MiniMax API

## 项目结构

```
travel-agent/
├── app.py                      # Streamlit 主应用
├── agent/
│   ├── services/
│   │   ├── itinerary_service.py     # 行程生成
│   │   └── llm_service.py           # 对话与描述生成
│   └── tools/
│       ├── search_attractions.py   # 景点搜索
│       ├── calculate_distance.py   # 距离计算
│       └── plan_route.py           # 路线规划
├── data/
│   └── attractions.json         # 景点数据库
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
cd travel-agent
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
export MINIMAX_API_KEY="your_minimax_api_key"  # 可选，用于更自然的聊天与描述
export GAODE_MAP_API_KEY="your_gaode_map_api_key"  # 可选，用于更精确的距离计算
```

### 3. 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中打开，默认地址: http://localhost:8501

## 使用方法

1. **设置目的地**: 在侧边栏输入目标城市
2. **选择天数**: 滑动选择旅行天数 (1-7天)
3. **设置人数**: 选择旅行人数
4. **选择偏好**: 勾选感兴趣的景点类型
5. **开始规划**: 点击按钮生成行程
6. **对话调整**: 在右侧聊天框提出调整要求

## 示例问题

- "可以增加一些拍照好看的景点吗？"
- "第2天的行程太紧了，能轻松一点吗？"
- "有什么美食推荐？"
- "各个景点之间怎么去？"

## 注意事项

- MiniMax API Key 为可选配置
- 高德地图 API Key 可选，用于更精确的距离计算
- 景点数据库包含中国主要城市的热门景点
- 行程规划基于贪心算法，可能不是最优解

## 许可证

MIT License
