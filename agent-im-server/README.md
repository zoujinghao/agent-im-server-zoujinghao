# Agent IM Server

A complete Agent conversation service with IM capabilities and Agent execution engine, built with Python and FastAPI.

## 项目简介

本项目实现了一个支持工具调用的Agent会话服务，包含IM基础能力和Agent执行引擎。服务提供RESTful API用于会话管理、消息发送/接收，以及WebSocket实时推送功能。Agent引擎能够处理LLM工具调用，执行预注册的工具函数，并通过循环机制直到获得纯文本回复。

## 技术选型理由

- **Python**: 开发效率高，丰富的AI/ML生态系统，适合快速原型开发
- **FastAPI**: 高性能异步Web框架，自动生成API文档，类型安全
- **SQLite**: 轻量级嵌入式数据库，无需额外服务，适合单机部署
- **WebSockets**: 实现实时双向通信，支持流式事件推送
- **AsyncIO**: 异步编程模型，高效处理并发连接

## 架构说明

```
agent-im-server/
├── app/
│   ├── api/          # RESTful API路由
│   ├── agent/        # Agent执行引擎
│   ├── db/           # 数据库操作
│   ├── models/       # 数据模型
│   ├── tools/        # 工具注册和实现
│   ├── websocket/    # WebSocket连接管理
│   └── main.py       # 应用入口
├── tests/            # 测试文件
├── requirements.txt  # 依赖列表
├── .env.example      # 环境变量示例
└── README.md         # 项目文档
```

### 核心组件

1. **Database Layer**: SQLite数据库存储会话、消息和工具调用记录
2. **Tool Registry**: 工具注册中心，支持动态注册和JSON Schema验证
3. **Agent Engine**: Agent执行引擎，支持工具调用循环、并行执行和超时控制
4. **Connection Manager**: WebSocket连接管理，支持多端广播
5. **Authentication**: API Key认证系统
6. **API Routes**: RESTful API和WebSocket端点

## 启动步骤

1. 克隆仓库：
   ```bash
   git clone <repository-url>
   cd agent-im-server
   ```

2. 创建虚拟环境并安装依赖：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. 复制环境变量文件：
   ```bash
   cp .env.example .env
   # 编辑.env文件配置实际参数
   # 特别注意设置 AUTH_ENABLED=true 和 API_KEY=your-secret-key
   ```

4. 启动服务器：
   ```bash
   python main.py
   ```

5. 访问API文档：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### 会话管理
- `POST /conversations` - 创建新会话
- `GET /conversations` - 列出所有会话

### 消息管理
- `GET /conversations/{id}/messages` - 获取消息（游标分页）
- `POST /conversations/{id}/messages` - 发送消息并触发Agent回复

### WebSocket
- `ws://localhost:8000/ws?conversation_id={id}` - 连接WebSocket进行实时通信

## 认证说明

所有RESTful API端点都需要API Key认证（除非在开发环境中禁用）。

**请求头**:
```http
X-API-Key: your-api-key-here
```

**环境变量配置**:
- `AUTH_ENABLED=true` - 启用认证（生产环境推荐）
- `AUTH_ENABLED=false` - 禁用认证（开发环境）
- `API_KEY=your-secret-key` - 设置API密钥

## 已完成功能

✅ RESTful API - 会话创建、列出、消息获取和发送  
✅ WebSocket实时推送 - 支持同一会话多端广播  
✅ SQLite数据存储 - 完整的表结构设计  
✅ Agent执行引擎 - 支持工具调用循环  
✅ 工具注册系统 - 预置3个工具（天气、知识搜索、任务创建）  
✅ 流式事件推送 - tool_call、tool_result、text_delta、done事件  
✅ Token认证 - API Key认证系统  
✅ Graceful shutdown - 优雅关闭支持  
✅ 并发连接管理 - WebSocket连接池管理  
✅ 并行工具调用 - 支持多个工具同时执行  
✅ 工具超时控制 - 防止工具执行过久  

## 未完成功能

⚠️ 上下文持久化优化 - 可以添加缓存层提高性能  
⚠️ 真实LLM集成 - 当前使用Mock实现  

## 预置工具

1. **get_weather(city)**: 获取指定城市的天气信息
2. **search_knowledge(query)**: 在知识库中搜索信息
3. **create_task(title, assignee)**: 创建新任务并分配给指定人员

## 使用示例

### 创建会话（带认证）
```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"title": "My Conversation"}'
```

### 发送消息（带认证）
```bash
curl -X POST http://localhost:8000/conversations/1/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"content": "What is the weather in New York?"}'
```

### WebSocket连接
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?conversation_id=1');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## AI工具使用说明

本项目在开发过程中使用了AI辅助编程工具来提高开发效率。核心逻辑和架构设计均为手动实现，AI工具主要用于代码模板生成和语法检查。

## 安全注意事项

- 不要在生产环境中暴露`.env`文件
- 生产部署时应配置具体的CORS策略
- 建议始终启用身份验证（AUTH_ENABLED=true）
- 工具函数应进行输入验证和安全检查
- API密钥应定期轮换