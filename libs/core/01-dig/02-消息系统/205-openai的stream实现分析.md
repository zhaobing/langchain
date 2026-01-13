# OpenAI ChatModel `_stream` 方法实现分析

> 分析文件: `langchain_openai/chat_models/base.py`
> 方法位置: 第 1261-1330 行

## 一、方法概览

### 1.1 方法签名

```python
def _stream(
    self,
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    run_manager: CallbackManagerForLLMRun | None = None,
    *,
    stream_usage: bool | None = None,
    **kwargs: Any,
) -> Iterator[ChatGenerationChunk]:
```

### 1.2 核心职责

将 LangChain 的消息格式转换为 OpenAI API 的流式请求，处理响应流，并将每个数据块转换为 `ChatGenerationChunk` 返回。

---

## 二、执行流程

### 2.1 完整流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         _stream 方法执行流程                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 1. 前置准备阶段                                               │    │
│  │    - 确保同步客户端可用                                        │    │
│  │    - 设置 stream=True                                         │    │
│  │    - 确定是否需要 usage 元数据                                  │    │
│  │    - 构建 request payload                                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 2. 响应获取阶段 (两种路径)                                     │    │
│  │                                                              │    │
│  │   路径A: response_format 存在                                 │    │
│  │   └─> root_client.beta.chat.completions.stream()             │    │
│  │                                                              │    │
│  │   路径B: 普通 Chat Completions                                │    │
│  │     - include_response_headers=True:                          │    │
│  │       └─> client.with_raw_response.create() + parse()        │    │
│  │     - include_response_headers=False:                         │    │
│  │       └─> client.create()                                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 3. 流式处理阶段                                               │    │
│  │    - with context_manager 进入流式上下文                       │    │
│  │    - for chunk in response 遍历每个数据块                      │    │
│  │    - 转换 chunk 为 ChatGenerationChunk                        │    │
│  │    - 触发回调: run_manager.on_llm_new_token()                 │    │
│  │    - yield generation_chunk                                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 4. 完成处理阶段 (仅 response_format 模式)                      │    │
│  │    - response.get_final_completion() 获取最终响应              │    │
│  │    - 转换为 generation_chunk                                  │    │
│  │    - yield 最终 chunk                                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 详细步骤解析

#### 步骤 1: 前置准备 (1270-1277)

```python
self._ensure_sync_client_available()
kwargs["stream"] = True
stream_usage = self._should_stream_usage(stream_usage, **kwargs)
if stream_usage:
    kwargs["stream_options"] = {"include_usage": stream_usage}
payload = self._get_request_payload(messages, stop=stop, **kwargs)
default_chunk_class: type[BaseMessageChunk] = AIMessageChunk
base_generation_info = {}
```

| 操作 | 说明 |
|------|------|
| `_ensure_sync_client_available()` | 确保同步客户端已初始化，否则抛出异常 |
| `kwargs["stream"] = True` | 强制启用流式模式 |
| `_should_stream_usage()` | 按优先级确定是否流式输出 usage 元数据 |
| `_get_request_payload()` | 构建完整的 API 请求负载 |

#### 步骤 2: 响应获取 (1279-1295)

```python
if "response_format" in payload:
    # Beta API 流式路径 (Structured Output)
    if self.include_response_headers:
        warnings.warn("Cannot currently include response headers...")
    payload.pop("stream")
    response_stream = self.root_client.beta.chat.completions.stream(**payload)
    context_manager = response_stream
else:
    # 标准 Chat Completions 路径
    if self.include_response_headers:
        raw_response = self.client.with_raw_response.create(**payload)
        response = raw_response.parse()
        base_generation_info = {"headers": dict(raw_response.headers)}
    else:
        response = self.client.create(**payload)
    context_manager = response
```

**路径选择逻辑**:

| 条件 | 路径 | 说明 |
|------|------|------|
| `response_format` 存在 | Beta API | 用于结构化输出，不支持 headers |
| `include_response_headers=True` | with_raw_response | 获取原始响应头 |
| 其他 | 普通 create | 标准流式请求 |

#### 步骤 3: 流式处理 (1296-1318)

```python
try:
    with context_manager as response:
        is_first_chunk = True
        for chunk in response:
            if not isinstance(chunk, dict):
                chunk = chunk.model_dump()

            generation_chunk = self._convert_chunk_to_generation_chunk(
                chunk,
                default_chunk_class,
                base_generation_info if is_first_chunk else {},
            )
            if generation_chunk is None:
                continue

            default_chunk_class = generation_chunk.message.__class__
            logprobs = (generation_chunk.generation_info or {}).get("logprobs")

            if run_manager:
                run_manager.on_llm_new_token(
                    generation_chunk.text,
                    chunk=generation_chunk,
                    logprobs=logprobs,
                )
            is_first_chunk = False
            yield generation_chunk
```

**关键处理点**:

1. **数据格式转换**: Pydantic 对象转为 dict
2. **chunk 转换**: 调用 `_convert_chunk_to_generation_chunk()`
3. **类型跟踪**: 动态更新 `default_chunk_class`
4. **回调触发**: 通过 `run_manager` 通知新 token
5. **首次处理**: 仅在首个 chunk 附加 `base_generation_info`

#### 步骤 4: 完成处理 (1319-1330)

```python
except openai.BadRequestError as e:
    _handle_openai_bad_request(e)

# 仅 Beta API (response_format) 执行
if hasattr(response, "get_final_completion") and "response_format" in payload:
    final_completion = response.get_final_completion()
    generation_chunk = self._get_generation_chunk_from_completion(
        final_completion
    )
    if run_manager:
        run_manager.on_llm_new_token(
            generation_chunk.text, chunk=generation_chunk
        )
    yield generation_chunk
```

---

## 三、核心辅助方法

### 3.1 `_convert_chunk_to_generation_chunk` (1061-1121)

```python
def _convert_chunk_to_generation_chunk(
    self,
    chunk: dict,
    default_chunk_class: type,
    base_generation_info: dict | None,
) -> ChatGenerationChunk | None:
```

**职责**: 将 OpenAI API 返回的单个 chunk 转换为 LangChain 的 `ChatGenerationChunk`

**处理逻辑**:

```
                    ┌─────────────────┐
                    │   输入: chunk   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ type ==         │──── Yes ──> return None
                    │ content.delta?  │
                    └────────┬────────┘
                             │ No
                             ▼
                    ┌─────────────────┐
                    │ 提取 token_usage│
                    │ 和 choices      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ len(choices)    │
                    │ == 0?           │──── Yes ──> 返回空 content chunk
                    └────────┬────────┘              (带 usage_metadata)
                             │ No
                             ▼
                    ┌─────────────────┐
                    │ choice[delta]   │──── Yes ──> return None
                    │ is None?        │
                    └────────┬────────┘
                             │ No
                             ▼
                    ┌─────────────────┐
                    │ _convert_delta_  │
                    │ to_message_chunk │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 提取 finish_reason, │
                    │ model_name,       │
                    │ system_fingerprint,│
                    │ logprobs 等        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 返回            │
                    │ ChatGenerationChunk │
                    └─────────────────┘
```

**关键数据提取**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `usage_metadata` | `chunk.usage` + `service_tier` | token 使用情况 |
| `content` | `choice.delta.content` | 消息内容 |
| `tool_calls` | `choice.delta.tool_calls` | 工具调用 |
| `finish_reason` | `choice.finish_reason` | 结束原因 |
| `logprobs` | `choice.logprobs` | 对数概率 |
| `model_name` | `chunk.model` | 模型名称 |

### 3.2 `_convert_delta_to_message_chunk` (362-415)

```python
def _convert_delta_to_message_chunk(
    _dict: Mapping[str, Any],
    default_class: type[BaseMessageChunk]
) -> BaseMessageChunk:
```

**职责**: 根据 delta 的 role 和内容，创建对应类型的 MessageChunk

**角色映射**:

| OpenAI Role | LangChain 类型 | 构造参数 |
|-------------|----------------|----------|
| `user` | `HumanMessageChunk` | content, id |
| `assistant` | `AIMessageChunk` | content, additional_kwargs, id, tool_call_chunks |
| `system` / `developer` | `SystemMessageChunk` | content, id, additional_kwargs |
| `function` | `FunctionMessageChunk` | content, name, id |
| `tool` | `ToolMessageChunk` | content, tool_call_id, id |
| 其他 | `ChatMessageChunk` / `default_class` | content, role, id |

### 3.3 `_should_stream_usage` (1242-1259)

```python
def _should_stream_usage(
    self, stream_usage: bool | None = None, **kwargs: Any
) -> bool:
```

**职责**: 按优先级确定是否在流式输出中包含 usage 元数据

**优先级顺序** (从高到低):

1. 方法参数 `stream_usage`
2. `kwargs.stream_options.include_usage`
3. `self.model_kwargs.stream_options.include_usage`
4. `self.stream_usage` (实例属性)

### 3.4 `_get_generation_chunk_from_completion` (2185-2205)

```python
def _get_generation_chunk_from_completion(
    self, completion: openai.BaseModel
) -> ChatGenerationChunk:
```

**职责**: 用于 Beta API (response_format) 获取最终完整响应

**处理逻辑**:

1. 调用 `_create_chat_result()` 获取完整结果
2. 提取 `usage_metadata`（仅 AIMessage）
3. 移除 `tool_calls`（已在流中发送）
4. 构造空的 `AIMessageChunk`，携带 metadata
5. 返回 `ChatGenerationChunk`

---

## 四、技术要点

### 4.1 生成器模式

```python
def _stream(...) -> Iterator[ChatGenerationChunk]:
    # ...
    for chunk in response:
        # 处理...
        yield generation_chunk
```

**设计模式**: Python Generator

**优势**:
- 惰性计算，节省内存
- 支持实时流式输出
- 与 LangChain 的 `Runnable.stream()` 自然集成

### 4.2 上下文管理器

```python
with context_manager as response:
    for chunk in response:
        # 处理...
```

**作用**:
- 自动管理资源 (HTTP 连接)
- 异常安全
- 支持 Beta API 的特殊流式接口

### 4.3 动态类型跟踪

```python
default_chunk_class: type[BaseMessageChunk] = AIMessageChunk
# ...
for chunk in response:
    generation_chunk = self._convert_chunk_to_generation_chunk(
        chunk,
        default_chunk_class,
        base_generation_info if is_first_chunk else {},
    )
    default_chunk_class = generation_chunk.message.__class__
```

**目的**: 保持消息类型一致性，处理响应中角色切换的情况

### 4.4 回调机制

```python
if run_manager:
    run_manager.on_llm_new_token(
        generation_chunk.text,
        chunk=generation_chunk,
        logprobs=logprobs,
    )
```

**触发时机**: 每个 yield 之前

**作用**:
- 可观测性
- 日志记录
- 自定义处理逻辑

### 4.5 错误处理

```python
try:
    # 流式处理...
except openai.BadRequestError as e:
    _handle_openai_bad_request(e)
```

**处理类型**: 专门的 OpenAI 错误处理

### 4.6 双路径设计

```
                    ┌─────────────────────┐
                    │   request payload   │
                    └──────────┬──────────┘
                               │
                     ┌─────────┴─────────┐
                     │ response_format?   │
                     └─────────┬─────────┘
                    Yes │       │ No
┌───────────────────────┘       └───────────────────────┐
│                                                   │
▼                                                   ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│ Beta API                    │     │ Standard Chat Completions   │
│ - beta.chat.completions     │     │ - client.create()           │
│   .stream()                 │     │ - with_raw_response.create()│
│ - get_final_completion()    │     │                            │
└─────────────────────────────┘     └─────────────────────────────┘
```

| 路径 | 用途 | 特点 |
|------|------|------|
| Beta API | Structured Output | 支持 JSON Schema，特殊流式接口 |
| Standard API | 普通对话 | 更成熟，支持响应头 |

---

## 五、数据流转

### 5.1 输入数据结构

```
messages: list[BaseMessage]
    │
    │ _get_request_payload()
    ▼
payload: dict
{
    "messages": [...],
    "stream": True,
    "stream_options": {"include_usage": True},
    "model": "...",
    ...
}
```

### 5.2 输出数据结构

```
OpenAI Response Chunk (SSE)
    │
    │ for chunk in response
    ▼
chunk: dict
{
    "id": "...",
    "choices": [{
        "delta": {"content": "...", "role": "assistant"},
        "finish_reason": null,
        ...
    }],
    "usage": {...}
}
    │
    │ _convert_chunk_to_generation_chunk()
    ▼
generation_chunk: ChatGenerationChunk
{
    "message": AIMessageChunk(content="..."),
    "generation_info": {
        "finish_reason": "stop",
        "model_name": "gpt-4",
        ...
    }
}
```

### 5.3 Message Chunk 继承

```
BaseMessageChunk (langchain_core.messages)
    │
    ├── AIMessageChunk
    ├── HumanMessageChunk
    ├── SystemMessageChunk
    ├── ToolMessageChunk
    └── FunctionMessageChunk
```

---

## 六、使用示例

### 6.1 基本流式调用

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")

# 流式输出
for chunk in llm.stream("Hello, how are you?"):
    print(chunk.content, end="")
```

### 6.2 带回调的流式调用

```python
from langchain.callbacks import CallbackManager

class MyCallbackHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(f"Token: {token}")

llm = ChatOpenAI(
    model="gpt-4",
    callbacks=[MyCallbackHandler()]
)

for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="")
```

### 6.3 获取 usage 元数据

```python
llm = ChatOpenAI(
    model="gpt-4",
    stream_usage=True
)

for chunk in llm.stream("Count to 10"):
    if hasattr(chunk.message, 'usage_metadata') and chunk.message.usage_metadata:
        print(f"\nUsage: {chunk.message.usage_metadata}")
```

---

## 七、关键设计决策

### 7.1 为什么分离 `_stream` 和 `_stream_responses`?

| 方法 | 用途 |
|------|------|
| `_stream()` | 标准 Chat Completions API |
| `_stream_responses()` | OpenAI Responses API (新功能) |

### 7.2 为什么需要 `default_chunk_class` 动态更新?

为了处理多角色对话场景，保持消息类型一致性：

```python
default_chunk_class = AIMessageChunk  # 初始

# 如果响应中出现 system 消息
# next chunk 可能是 SystemMessageChunk
default_chunk_class = generation_chunk.message.__class__  # 更新
```

### 7.3 为什么 `is_first_chunk` 只附加一次 metadata?

避免重复信息，`base_generation_info` (如 headers) 只需要在第一个 chunk 中出现。

---

## 八、相关文件引用

| 文件 | 说明 |
|------|------|
| `langchain_core/messages/base.py` | BaseMessage 及其子类定义 |
| `langchain_core/language_models/chat_models.py` | BaseChatModel 抽象类 |
| `langchain_core/callbacks/manager.py` | CallbackManagerForLLMRun |
| `langchain_core/generation/chat.py` | ChatGenerationChunk 定义 |
