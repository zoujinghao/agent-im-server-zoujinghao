# Agent IM Server

A complete Agent conversation service with IM capabilities and Agent execution engine, built with Python and FastAPI.

## 项目简介

本项目实现了一个支持工具调用的Agent会话服务，包含IM基础能力和Agent执行引擎。服务提供RESTful API用于会话管理、消息发送/接收，以及WebSocket实时推送功能。Agent引擎能够处理LLM工具调用，执行预注册的工具函数，并通过循环机制直到获得纯文本回复。

系统采用模块化设计，包含数据库层、工具注册中心、Agent执行引擎、WebSocket连接管理、认证系统等核心组件，确保高内聚低耦合的架构。

## 技术选型理由

- **Python**: 开发效率高，丰富的AI/ML生态系统，适合快速原型开发和Agent系统构建
- **FastAPI**: 高性能异步Web框架，自动生成交互式API文档，类型安全，支持WebSocket
- **SQLite**: 轻量级嵌入式数据库，无需额外服务，单文件存储，适合单机部署和开发测试
- **WebSockets**: 实现实时双向通信，支持流式事件推送和多端同步
- **AsyncIO**: 异步编程模型，高效处理并发连接和并行工具调用
- **python-dotenv**: 安全的环境变量管理，支持敏感信息配置

## 架构说明

```
agent-im-server/
├── app/
│   ├── agent/        # Agent执行引擎 - 核心业务逻辑
│   │   └── agent_engine.py    # Agent循环、工具调用、超时控制
│   ├── api/          # API接口层
│   │   ├── auth.py            # API Key认证系统
│   │   └── routes.py          # RESTful API和WebSocket路由
│   ├── db/           # 数据库层
│   │   └── database.py        # SQLite数据库操作封装
│   ├── models/       # 数据模型
│   │   └── models.py          # Conversation、Message、ToolCallRecord模型
│   ├── tools/        # 工具层
│   │   └── tool_registry.py   # 工具注册中心和预置工具实现
│   ├── websocket/    # WebSocket层
│   │   └── connection_manager.py  # 连接管理、广播、多端同步
│   └── main.py       # 应用入口和依赖注入
├── requirements.txt  # 项目依赖
├── .env.example      # 环境变量配置示例
├── .env              # 实际环境变量（已配置安全API key）
├── README.md         # 项目文档
└── resume.md         # 个人简历
```

### 核心组件详细说明

#### 1. Database Layer (SQLite)
- **conversations表**: 存储会话信息（id, title, created_at）
- **messages表**: 存储消息记录（conversation_id, sender_type, content, created_at, tool_calls）
- **tool_call_records表**: 存储工具调用详情（message_id, tool_name, arguments, result, duration_ms, created_at）
- 支持游标分页查询，避免大数据量性能问题
- 外键约束确保数据完整性

#### 2. Tool Registry
- 动态工具注册机制，支持运行时添加新工具
- JSON Schema验证确保工具参数正确性
- 预置3个实用工具：
  - `get_weather(city)`: 获取指定城市天气信息
  - `search_knowledge(query)`: 知识库搜索
  - `create_task(title, assignee)`: 任务创建和分配

#### 3. Agent Engine
- **Agent Loop**: 最大10次迭代防止无限循环
- **并行工具调用**: 使用asyncio.gather同时执行多个工具
- **超时控制**: 每个工具调用30秒超时保护
- **Mock LLM**: 模拟真实LLM行为，支持工具调用和纯文本响应
- **事件驱动**: 通过回调函数推送实时事件

#### 4. Connection Manager
- **多端广播**: 同一会话支持多个客户端连接
- **自动清理**: 自动移除断开的连接
- **错误处理**: 健壮的异常处理确保服务稳定性

#### 5. Authentication
- **API Key认证**: HTTP Header `X-API-Key` 验证
- **灵活配置**: 可通过环境变量启用/禁用认证
- **生产就绪**: 默认启用认证，确保API安全性

## 启动步骤

### 1. 环境准备
```bash
# 克隆仓库（如果是从GitHub克隆）
git clone <repository-url>
cd agent-im-server-zoujinghao

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量
项目已预配置安全的API key，但您可以根据需要修改：

**.env文件内容:**
```env
# 认证配置（已启用）
AUTH_ENABLED=true
API_KEY=sk_agent_im_8f2e9b1c7d3a6e5f4c2b1a9d8e7f6c5b4a3c2d1e

# 数据库配置
DATABASE_PATH=agent_im_server.db

# 服务器配置
HOST=0.0.0.0
PORT=8080

# Agent配置
MAX_AGENT_ITERATIONS=10
TOOL_TIMEOUT=30
```

### 3. 启动服务器
```bash
# 在agent-im-server-zoujinghao目录下运行
python main.py
```

### 4. 验证启动
- **根路径**: http://localhost:8080
- **API文档**: http://localhost:8080/docs (Swagger UI)
- **ReDoc文档**: http://localhost:8080/redoc

## API Endpoints 详细说明

### 会话管理
- `POST /conversations` 
  - **功能**: 创建新会话
  - **请求体**: `{"title": "可选标题"}`
  - **响应**: `{"id": 1, "title": "会话标题"}`

- `GET /conversations`
  - **功能**: 列出所有会话（按创建时间倒序）
  - **响应**: 会话列表数组

### 消息管理
- `GET /conversations/{id}/messages`
  - **功能**: 获取指定会话的消息（游标分页）
  - **查询参数**: `limit` (默认50, 范围1-100), `cursor` (分页游标)
  - **响应**: `{"messages": [...], "next_cursor": 123}`

- `POST /conversations/{id}/messages`
  - **功能**: 发送消息并触发Agent回复
  - **请求体**: `{"content": "用户消息内容"}`
  - **响应**: Agent回复消息信息
  - **副作用**: 触发WebSocket实时事件推送

### WebSocket 实时通信
- `ws://localhost:8080/ws?conversation_id={id}`
  - **连接参数**: `conversation_id` (必需)
  - **推送事件类型**:
    - `tool_call`: 工具调用开始
    - `tool_result`: 工具执行结果  
    - `text_delta`: Agent回复流式片段
    - `done`: 对话完成，包含完整回复

## 认证说明

所有RESTful API端点都需要API Key认证（已默认启用）。

**请求头格式**:
```http
X-API-Key: sk_agent_im_8f2e9b1c7d3a6e5f4c2b1a9d8e7f6c5b4a3c2d1e
```

**环境变量配置**:
- `AUTH_ENABLED=true` - 启用认证（生产环境推荐，默认已启用）
- `AUTH_ENABLED=false` - 禁用认证（仅开发环境使用）
- `API_KEY=your-secret-key` - 设置API密钥（已配置安全密钥）

## 功能完成情况

### ✅ 已完成功能（完全符合实战题要求）

**Part A：会话与消息**
- ✅ RESTful API - 会话创建、列出、消息获取（游标分页）、消息发送
- ✅ WebSocket实时推送 - 支持同一会话多端广播
- ✅ SQLite数据存储 - 完整表结构，包含sender_type、content、created_at、conversation_id
- ✅ 工具调用记录落库 - tool_name、arguments、result、耗时全部记录

**Part B：Agent执行引擎**
- ✅ Agent Loop - 会话历史处理，工具调用循环，最大10次防无限循环
- ✅ 工具注册 - 预置3个工具（天气、知识搜索、任务创建），JSON Schema验证
- ✅ 流式事件推送 - tool_call、tool_result、text_delta、done四种事件类型

**加分项实现**
- ✅ Token认证 - API Key认证系统（已启用）
- ✅ Graceful shutdown - 优雅关闭支持（SIGINT/SIGTERM信号处理）
- ✅ 并发连接管理 - WebSocket连接池，自动清理断开连接
- ✅ 并行工具调用 - asyncio.gather支持多个工具同时执行
- ✅ 工具超时控制 - 30秒超时保护，防止工具执行过久

### ⚠️ 待优化功能
- **上下文持久化优化** - 可添加Redis缓存层提高性能
- **真实LLM集成** - 当前使用Mock实现，可替换为OpenAI/兼容API

## 预置工具详细说明

### 1. get_weather(city)
- **功能**: 获取指定城市的天气信息
- **参数**: `city` (string, 必需) - 城市名称
- **返回**: `"Current weather in {city}: 22°C, sunny"`
- **使用示例**: "What is the weather in Beijing?"

### 2. search_knowledge(query)
- **功能**: 在知识库中搜索相关信息
- **参数**: `query` (string, 必需) - 搜索关键词
- **返回**: 包含搜索结果的模拟响应
- **使用示例**: "Search for information about AI agents"

### 3. create_task(title, assignee)
- **功能**: 创建新任务并分配给指定人员
- **参数**: 
  - `title` (string, 必需) - 任务标题
  - `assignee` (string, 必需) - 负责人姓名
- **返回**: 任务创建确认信息
- **使用示例**: "Create a task to implement user authentication"

## 使用示例

### 1. 创建会话（带认证）
```bash
curl -X POST http://localhost:8080/conversations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_agent_im_8f2e9b1c7d3a6e5f4c2b1a9d8e7f6c5b4a3c2d1e" \
  -d '{"title": "Weather Inquiry"}'
```

### 2. 发送消息触发工具调用
```bash
curl -X POST http://localhost:8080/conversations/1/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_agent_im_8f2e9b1c7d3a6e5f4c2b1a9d8e7f6c5b4a3c2d1e" \
  -d '{"content": "What is the weather in New York?"}'
```

### 3. WebSocket实时监听
```javascript
// JavaScript客户端示例
const ws = new WebSocket('ws://localhost:8080/ws?conversation_id=1');

ws.onopen = () => {
    console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received event:', data.type, data.data);
    
    switch(data.type) {
        case 'tool_call':
            console.log('Tool called:', data.data.tool_name);
            break;
        case 'tool_result':
            console.log('Tool result:', data.data.result);
            break;
        case 'text_delta':
            console.log('Agent response:', data.data.content);
            break;
        case 'done':
            console.log('Conversation completed:', data.data.content);
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('WebSocket disconnected');
};
```

## 数据库表结构

### conversations表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 会话ID |
| title | TEXT NOT NULL | 会话标题 |
| created_at | TIMESTAMP | 创建时间 |

### messages表  
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 消息ID |
| conversation_id | INTEGER NOT NULL | 关联会话ID |
| sender_type | TEXT NOT NULL | 发送者类型(user/agent) |
| content | TEXT NOT NULL | 消息内容 |
| created_at | TIMESTAMP | 创建时间 |
| tool_calls | TEXT | 工具调用JSON数组 |

### tool_call_records表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 记录ID |
| message_id | INTEGER NOT NULL | 关联消息ID |
| tool_name | TEXT NOT NULL | 工具名称 |
| arguments | TEXT NOT NULL | 调用参数(JSON) |
| result | TEXT NOT NULL | 执行结果 |
| duration_ms | INTEGER NOT NULL | 执行耗时(毫秒) |
| created_at | TIMESTAMP | 创建时间 |

## AI工具使用说明

本项目在开发过程中使用了AI辅助编程工具来提高开发效率。核心逻辑和架构设计均为手动实现，AI工具主要用于：
- 代码模板生成和语法检查
- 文档编写和格式化
- 错误检测和修复建议

所有关键业务逻辑（Agent引擎、工具注册、WebSocket管理等）均为自主实现，确保对代码的完全理解和掌控。

## 安全注意事项

- 🔒 **API密钥保护**: `.env`文件包含敏感信息，请勿提交到版本控制系统
- 🛡️ **认证默认启用**: 生产环境务必保持`AUTH_ENABLED=true`
- 📊 **输入验证**: 所有API端点都有基本的输入验证和错误处理
- ⏱️ **超时保护**: 工具调用有30秒超时，防止恶意或错误调用导致服务阻塞
- 🧹 **资源清理**: WebSocket连接和数据库连接都有完善的清理机制

## 性能特性

- **异步非阻塞**: 基于AsyncIO，支持高并发连接
- **内存高效**: SQLite单文件存储，无额外内存开销
- **流式处理**: WebSocket实时推送，避免轮询开销
- **并行执行**: 工具调用并行处理，减少总响应时间

## 部署建议

- **开发环境**: 直接运行`python main.py`
- **生产环境**: 
  - 使用Gunicorn + Uvicorn工作进程
  - 配置反向代理(Nginx/Apache)
  - 设置适当的CORS策略（当前为开发便利设置为"*"）
  - 定期备份SQLite数据库文件