# Runnable 协议的 invoke 与 run 分层设计总结

## 概述

LangChain 的核心设计哲学是将所有组件（包括 Tool）标准化为"可运行单元"（Runnable）。这种设计通过统一的 `Runnable` 协议实现，提供了 `invoke` 和 `run` 两层接口：

- **`invoke()`**: Runnable 协议的标准化接口，面向未来的统一调用方式
- **`run()`**: Tool 特有的接口，提供更细粒度的参数控制，保持向后兼容

这种分层设计使 LangChain 能够在保持向后兼容的同时，提供现代化的组合式编程体验（LCEL）。

---

## 一、Runnable 协议基础

### 1.1 Runnable 类定义

`Runnable` 是 LangChain 的基础抽象，定义在 `langchain_core/runnables/base.py`：

```python
class Runnable(ABC, Generic[Input, Output]):
    """可被调用、批处理、流式处理、转换和组合的工作单元。

    核心方法：
    - invoke/ainvoke: 将单个输入转换为输出
    - batch/abatch: 高效地将多个输入转换为输出
    - stream/astream: 从单个输入流式输出
    - astream_log: 流式输出选定的中间结果
    """
```

### 1.2 继承体系

```
Runnable (ABC, Generic[Input, Output])
    ├── 定义执行接口协议
    ├── 支持组合操作（| 操作符）
    └── 提供批处理和流式处理

Serializable (Pydantic BaseModel)
    ├── 提供序列化/反序列化
    └── 自动验证和类型安全

RunnableSerializable (继承两者)
    ├── 结合 Runnable 的执行能力
    └── 结合 Serializable 的持久化能力
         │
         ▼
    BaseTool (继承 RunnableSerializable)
    ├── Tool 变为第一类 Runnable
    └── 实现 invoke() 和 run() 双接口
```

### 1.3 RunnableConfig 结构

`RunnableConfig` 是 Runnable 协议的核心配置对象，统一管理所有运行时配置：

```python
class RunnableConfig(TypedDict, total=False):
    # 可观察性
    tags: list[str]                    # 用于过滤调用的标签
    metadata: dict[str, Any]           # JSON 可序列化的元数据
    callbacks: Callbacks                # 回调处理器

    # 调试和追踪
    run_name: str                      # 追踪运行的名称
    run_id: uuid.UUID | None          # 唯一运行标识符

    # 执行控制
    max_concurrency: int | None        # 最大并行调用数
    recursion_limit: int               # 最大递归深度（默认 25）

    # 运行时配置
    configurable: dict[str, Any]        # 可配置字段的运行时值
```

**设计优势：**
- 所有配置集中在一个对象中
- 易于传播和合并
- 类型安全（TypedDict）
- 支持部分配置和默认值

---

## 二、invoke vs run 深度对比

### 2.1 方法签名对比

| 方面 | `invoke()` | `run()` |
|------|------------|---------|
| **接口类型** | Runnable 协议方法 | Tool 特有方法 |
| **参数数量** | 2 个 (input, config) | 12+ 个 |
| **配置方式** | 统一的 RunnableConfig | 分散的独立参数 |
| **输入类型** | `str \| dict \| ToolCall` | `str \| dict` |
| **回调处理** | 自动通过 config 传播 | 手动传递 callbacks 参数 |
| **可组合性** | 支持 `|` 操作符 | 不可组合 |
| **异步支持** | `ainvoke()` 自动桥接 | `arun()` 需显式实现 |

### 2.2 完整方法签名

```python
# Runnable 协议 - invoke()
def invoke(
    self,
    input: str | dict | ToolCall,
    config: RunnableConfig | None = None,
    **kwargs: Any,
) -> Any:
    """统一的 Runnable 调用接口"""

# Tool 特有 - run()
def run(
    self,
    tool_input: str | dict[str, Any],
    verbose: bool | None = None,
    start_color: str | None = "green",
    color: str | None = "green",
    callbacks: Callbacks = None,
    *,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    run_name: str | None = None,
    run_id: uuid.UUID | None = None,
    config: RunnableConfig | None = None,
    tool_call_id: str | None = None,
    **kwargs: Any,
) -> Any:
    """Tool 特有的详细参数接口"""
```

### 2.3 实现关系

```python
# BaseTool 中的实现
class BaseTool(RunnableSerializable[str | dict | ToolCall, Any]):
    @override
    def invoke(
        self,
        input: str | dict | ToolCall,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Any:
        # invoke() 实际上委托给 run()
        tool_input, kwargs = _prep_run_args(input, config, **kwargs)
        return self.run(tool_input, **kwargs)

    def run(self, tool_input: str | dict, **kwargs) -> Any:
        # run() 包含完整的执行逻辑
        # 1. 回调管理
        callback_manager = CallbackManager.configure(...)
        # 2. 输入解析
        parsed_input = self._parse_input(tool_input, tool_call_id)
        # 3. 工具执行
        response = self._run(*args, **kwargs)
        # 4. 输出格式化
        return _format_output(response, ...)
```

**关键发现：** `invoke()` 是 `run()` 的简化包装器，所有实际执行逻辑都在 `run()` 中。

---

## 三、执行流程对比

### 3.1 invoke() 执行流程

```
invoke(input, config)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 配置准备 (_prep_run_args)                                │
│   - 从 ToolCall 提取 tool_input 和 tool_call_id             │
│   - 合并 RunnableConfig 中的 callbacks, tags, metadata      │
│   - 创建统一的 kwargs 字典                                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 委托给 run()                                              │
│   - 将处理后的参数传递给 run()                              │
│   - run() 负责实际的执行逻辑                                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                          返回结果
```

### 3.2 run() 执行流程

```
run(tool_input, callbacks, tags, metadata, ...)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 回调管理器配置                                            │
│   callback_manager = CallbackManager.configure(            │
│       callbacks, self.callbacks, verbose,                  │
│       tags, self.tags, metadata, self.metadata            │
│   )                                                        │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 回调启动 (on_tool_start)                                 │
│   - 过滤注入参数                                            │
│   - 触发 on_tool_start 回调                                │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 输入解析与验证 (_parse_input)                             │
│   - 字符串/字典输入验证                                     │
│   - 使用 args_schema 进行 Pydantic 验证                    │
│   - 注入运行时参数 (tool_call_id 等)                        │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 参数转换 (_to_args_and_kwargs)                            │
│   - 将输入转换为位置参数和关键字参数                         │
│   - 注入 run_manager 和 config                             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 工具执行 (_run)                                           │
│   - 在配置上下文中执行                                      │
│   - 传递 run_manager 用于追踪                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. 错误处理                                                  │
│   - ValidationError → handle_validation_error              │
│   - ToolException → handle_tool_error                      │
│   - 其他异常 → 直接抛出                                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. 输出格式化 (_format_output)                               │
│   - 根据 response_format 格式化                             │
│   - 构建 ToolMessage (如果有 tool_call_id)                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. 回调结束 (on_tool_end)                                    │
│   - 触发 on_tool_end 回调                                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                          返回结果
```

---

## 四、设计哲学

### 4.1 分层设计原则

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application)                     │
│                                                             │
│  用户代码使用 LCEL 组合组件                                 │
│  chain = prompt | model | tool | parser                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Runnable 协议层 (Protocol)                 │
│                                                             │
│  统一的 invoke() 接口                                       │
│  - 标准化配置 (RunnableConfig)                              │
│  - 可组合性 (| 操作符)                                      │
│  - 自动配置传播                                             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Tool 实现层 (Implementation)               │
│                                                             │
│  详细的 run() 接口                                          │
│  - 细粒度参数控制                                           │
│  - 完整的执行逻辑                                           │
│  - 向后兼容性                                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  核心执行层 (Core Execution)                │
│                                                             │
│  _run() / _arun() 抽象方法                                  │
│  - 子类实现具体逻辑                                         │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 核心设计目标

| 目标 | 实现方式 |
|------|----------|
| **统一接口** | Runnable 协议定义标准方法签名 |
| **可组合性** | `|` 操作符支持声明式组合 |
| **配置传播** | RunnableConfig 自动在链中传递 |
| **向后兼容** | 保留 `run()` 方法支持旧代码 |
| **类型安全** | 泛型 `Runnable[Input, Output]` |
| **可观测性** | 内置 Callback 系统 |

### 4.3 Tool 作为 Runnable 的优势

```python
# 1. Tool 可以使用 LCEL 组合
tool = search_tool
chain = prompt | model | tool | output_parser

# 2. Tool 自动获得批处理能力
results = tool.batch([query1, query2, query3])

# 3. Tool 自动获得流式处理能力
for chunk in tool.stream(large_query):
    process(chunk)

# 4. Tool 自动获得配置传播
result = tool.invoke(
    input,
    config={
        "callbacks": [my_tracer],
        "tags": ["production"],
        "metadata": {"user_id": "123"}
    }
)

# 5. Tool 可以转换为其他 Runnable
# Runnable → Tool
tool = convert_runnable_to_tool(my_runnable)
# Tool → Runnable (本身就是)
chain = tool | other_runnable
```

---

## 五、LCEL (LangChain Expression Language)

### 5.1 组合操作符

```python
# __or__ 操作符实现
def __or__(
    self,
    other: Runnable[Any, Other] | Callable[..., Other] | Mapping[str, ...],
) -> RunnableSerializable[Input, Other]:
    """Runnable 组合操作符"""
    return RunnableSequence(self, coerce_to_runnable(other))

# 使用示例
chain = prompt | model | parser
# 等价于
chain = RunnableSequence([prompt, model, parser])
```

### 5.2 RunnableSequence 执行

```python
class RunnableSequence(RunnableSerializable[Input, Output]):
    def invoke(
        self,
        input: Input,
        config: RunnableConfig | None = None,
        **kwargs: Any
    ) -> Output:
        input_ = input
        for i, step in enumerate(self.steps):
            # 每一步都获得补丁后的配置
            config = patch_config(
                config,
                callbacks=run_manager.get_child(f"seq:step:{i + 1}")
            )
            # 在配置上下文中执行
            with set_config_context(config) as context:
                input_ = context.run(step.invoke, input_, config, **kwargs)
        return input_
```

**关键特性：**
1. **配置自动传播**：每个步骤自动获得回调管理器的子节点
2. **上下文隔离**：使用 `ContextVar` 确保配置在异步环境中正确传播
3. **错误处理**：任何步骤的错误都会被正确传播

### 5.3 RunnableParallel 并发执行

```python
# 使用字典字面量创建并行执行
chain = (
    RunnableLambda(lambda x: x + 1) | {
        "mul_2": RunnableLambda(lambda x: x * 2),
        "mul_5": RunnableLambda(lambda x: x * 5),
    }
)

# 输入: 1
# 输出: {"mul_2": 4, "mul_5": 10}
```

---

## 六、配置传播机制

### 6.1 ContextVar 实现

```python
# 使用 Python 的 ContextVar 实现配置上下文
var_child_runnable_config: ContextVar[RunnableConfig | None] = ContextVar(
    "child_runnable_config", default=None
)

@contextmanager
def set_config_context(config: RunnableConfig):
    """设置子 Runnable 配置上下文"""
    ctx = copy_context()
    config_token, _ = ctx.run(_set_config_context, config)
    try:
        yield ctx
    finally:
        # 确保配置被正确清理
        ctx.run(var_child_runnable_config.reset, config_token)
```

### 6.2 配置合并策略

```python
def merge_configs(*configs: RunnableConfig | None) -> RunnableConfig:
    """合并多个配置"""
    base: RunnableConfig = {}
    for config in (ensure_config(c) for c in configs if c is not None):
        for key in config:
            if key == "metadata":
                # metadata 合并
                base["metadata"] = {
                    **base.get("metadata", {}),
                    **(config.get("metadata") or {})
                }
            elif key == "tags":
                # tags 去重合并
                base["tags"] = sorted(
                    set(base.get("tags", []) + (config.get("tags") or []))
                )
            elif key == "callbacks":
                # callbacks 特殊合并逻辑
                # ... 处理 list、manager 等不同情况
    return base
```

### 6.3 回调传播

```python
def patch_config(
    config: RunnableConfig | None,
    *,
    callbacks: BaseCallbackManager | None = None,
    ...
) -> RunnableConfig:
    """为特定步骤补丁配置"""
    config = ensure_config(config)
    if callbacks is not None:
        config["callbacks"] = callbacks
        # 替换 callbacks 时清除 run_name
        if "run_name" in config:
            del config["run_name"]
    return config

# 在 RunnableSequence 中使用
child_config = patch_config(
    config,
    callbacks=run_manager.get_child()  # 创建子回调管理器
)
```

---

## 七、异步支持

### 7.1 run_in_executor 桥接

```python
async def run_in_executor(
    executor_or_config: Executor | RunnableConfig | None,
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """在线程池中执行同步函数"""

    def wrapper() -> T:
        try:
            return func(*args, **kwargs)
        except StopIteration as exc:
            # StopIteration 不能在 asyncio.Future 上设置
            # 转换为 RuntimeError
            raise RuntimeError from exc

    if executor_or_config is None or isinstance(executor_or_config, dict):
        # 使用默认执行器，复制当前上下文
        return await asyncio.get_running_loop().run_in_executor(
            None,
            partial(copy_context().run, wrapper),
        )

    return await asyncio.get_running_loop().run_in_executor(
        executor_or_config, wrapper
    )
```

### 7.2 默认异步实现

```python
class BaseTool(RunnableSerializable[str | dict | ToolCall, Any]):
    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """默认异步实现：在线程池中运行同步版本"""
        # 将 run_manager 转换为同步版本
        if kwargs.get("run_manager"):
            kwargs["run_manager"] = kwargs["run_manager"].get_sync()
        # 在执行器中运行 _run
        return await run_in_executor(None, self._run, *args, **kwargs)
```

---

## 八、使用场景与最佳实践

### 8.1 使用 invoke() 的场景

```python
# ✅ 推荐：使用 invoke()

# 1. LCEL 组合
chain = prompt | model | tool | parser
result = chain.invoke({"query": "search"})

# 2. 需要配置传播
result = tool.invoke(
    input,
    config={
        "callbacks": [tracer],
        "tags": ["production"],
        "max_concurrency": 10
    }
)

# 3. 批处理
results = tool.batch([input1, input2, input3])

# 4. 流式处理
async for chunk in tool.astream(large_input):
    process(chunk)

# 5. 与其他 Runnable 组合
combined = tool1 | tool2 | tool3
```

### 8.2 使用 run() 的场景

```python
# ⚠️ 特殊情况：使用 run()

# 1. 需要详细的日志输出
result = tool.run(
    input,
    verbose=True,
    start_color="blue",
    color="green"
)

# 2. 精确控制回调
result = tool.run(
    input,
    callbacks=[specific_callback],
    tags=["custom-tag"],
    metadata={"key": "value"}
)

# 3. 指定 run_id 用于追踪
result = tool.run(
    input,
    run_id=uuid.uuid4(),
    run_name="custom_run_name"
)

# 4. 向后兼容旧代码
# 旧代码可能直接使用 run()
```

### 8.3 迁移指南

```python
# 旧代码 (使用 run())
result = tool.run(
    input_data,
    callbacks=[my_callback],
    tags=["production"],
    verbose=True
)

# 新代码 (使用 invoke())
result = tool.invoke(
    input_data,
    config={
        "callbacks": [my_callback],
        "tags": ["production"]
    }
)
# 注意：verbose 是 Tool 特有的，invoke() 不直接支持
```

---

## 九、实际应用示例

### 9.1 完整的 LCEL 链

```python
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """搜索 API"""
    return f"Results for: {query}"

@tool
def analyze(text: str) -> str:
    """分析文本"""
    return f"Analysis: {text[:50]}..."

# 创建完整的处理链
chain = (
    RunnableLambda(lambda x: x["query"])  # 提取查询
    | search                                # 搜索
    | analyze                               # 分析
)

# 使用 invoke 执行
result = chain.invoke(
    {"query": "langchain tutorials"},
    config={
        "callbacks": [ConsoleCallbackHandler()],
        "tags": ["research", "v1"],
        "metadata": {"user": "developer"}
    }
)
print(result)  # "Analysis: Results for: langchain tutorials..."
```

### 9.2 RunnableParallel 并行处理

```python
from langchain_core.runnables import RunnableParallel

# 并行执行多个工具
parallel_chain = RunnableParallel(
    search=search_tool,
    summarize=summary_tool,
    classify=classification_tool
)

# 单次 invoke 自动并行执行
results = parallel_chain.invoke({"text": "input text"})
# 输出: {"search": "...", "summarize": "...", "classify": "..."}
```

### 9.3 配置传播示例

```python
# 配置在整个链中传播
chain = prompt | model | tool

result = chain.invoke(
    input_data,
    config={
        "callbacks": [langchain_tracer],  # 传播到所有步骤
        "tags": ["experiment-123"],        # 所有步骤都有此标签
        "metadata": {"session": "abc"}     # 元数据传播
    }
)

# 每个步骤自动获得：
# - langchain_tracer 的子回调管理器
# - "experiment-123" 标签
# - {"session": "abc"} 元数据
```

---

## 十、总结

### 10.1 核心要点

| 方面 | 总结 |
|------|------|
| **设计目标** | 将所有组件标准化为 Runnable，实现统一接口 |
| **分层架构** | invoke()（协议层）→ run()（实现层）→ _run()（核心层） |
| **配置管理** | RunnableConfig 统一管理所有运行时配置 |
| **可组合性** | `|` 操作符支持声明式组合 |
| **异步支持** | 自动桥接同步和异步执行 |
| **向后兼容** | 保留 run() 接口支持旧代码 |

### 10.2 设计优势

1. **统一抽象**：所有组件（Model、Tool、Chain、Retriever）都是 Runnable
2. **可组合性**：通过 LCEL 轻松构建复杂流程
3. **自动传播**：配置和回调自动在链中传播
4. **类型安全**：泛型支持编译时类型检查
5. **可观测性**：内置追踪和回调系统
6. **性能优化**：自动批处理和并行执行

### 10.3 版本说明

- **langchain-core**: 1.1.1
- **核心文件**:
  - `langchain_core/runnables/base.py` - Runnable 基类
  - `langchain_core/runnables/config.py` - 配置管理
  - `langchain_core/tools/base.py` - BaseTool 实现

这种分层设计使 LangChain 能够在保持强大功能的同时，提供简洁优雅的开发体验，是现代 LLM 应用框架设计的典范。
