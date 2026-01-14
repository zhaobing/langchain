# DuckDuckGo Search 工具实现分析

本文档分析 `langchain_community.tools.ddg_search` 中 DuckDuckGo 搜索工具的实现方式。

## 源文件位置

```
langchain_community/tools/ddg_search/
├── __init__.py          # 导出接口
└── tool.py              # 工具实现

langchain_community/utilities/
└── duckduckgo_search.py # API 封装
```

## 实现模式分析

### 结论：**继承自 `BaseTool` 类**

DuckDuckGo 搜索工具采用**类继承**的方式实现，直接继承 `langchain_core.tools.BaseTool`。

```python
# tool.py:20-74
class DuckDuckGoSearchRun(BaseTool):
    """DuckDuckGo tool."""
    name: str = "duckduckgo_search"
    description: str = "..."
    api_wrapper: DuckDuckGoSearchAPIWrapper = Field(...)
    args_schema: Type[BaseModel] = DDGInput

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)
```

## 完整架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         DuckDuckGoSearchRun                     │
│                      (继承 BaseTool)                            │
├─────────────────────────────────────────────────────────────────┤
│  name: "duckduckgo_search"                                      │
│  description: "A wrapper around DuckDuckGo Search..."           │
│  args_schema: DDGInput                                          │
│  api_wrapper: DuckDuckGoSearchAPIWrapper                        │
├─────────────────────────────────────────────────────────────────┤
│  _run(query: str) -> str                                        │
│      └──> api_wrapper.run(query)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DuckDuckGoSearchAPIWrapper                   │
│                      (Pydantic BaseModel)                       │
├─────────────────────────────────────────────────────────────────┤
│  region: str = "wt-wt"                                          │
│  safesearch: str = "moderate"                                   │
│  time: str = "y"                                                │
│  max_results: int = 5                                           │
│  backend: str = "auto"                                          │
│  source: str = "text"                                           │
├─────────────────────────────────────────────────────────────────┤
│  run(query: str) -> str              │
│      └──> _ddgs_text/_ddgs_news/_ddgs_images                   │
│          └──> ddgs.text/news/images(...)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ddgs 库 (第三方)                         │
│                    from ddgs import DDGS                         │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件详解

### 1. DDGInput - 参数 Schema

```python
# tool.py:14-17
class DDGInput(BaseModel):
    """Input for the DuckDuckGo search tool."""
    query: str = Field(description="search query to look up")
```

使用 Pydantic `BaseModel` 定义工具的输入参数 schema，对应 JSON Schema：

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "search query to look up"
    }
  },
  "required": ["query"]
}
```

### 2. DuckDuckGoSearchRun - 基础工具

```python
# tool.py:20-74
class DuckDuckGoSearchRun(BaseTool):
    name: str = "duckduckgo_search"
    description: str = (
        "A wrapper around DuckDuckGo Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    api_wrapper: DuckDuckGoSearchAPIWrapper = Field(
        default_factory=DuckDuckGoSearchAPIWrapper
    )
    args_schema: Type[BaseModel] = DDGInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)
```

**关键点**：
- 继承 `BaseTool`，无需使用 `@tool` 装饰器
- 手动定义 `name`、`description`、`args_schema`
- `_run` 方法实现核心逻辑
- 通过 `api_wrapper` 委托给 API 封装类

### 3. DuckDuckGoSearchResults - 高级工具

```python
# tool.py:77-135
class DuckDuckGoSearchResults(BaseTool):
    name: str = "duckduckgo_results_json"
    description: str = "..."
    max_results: int = Field(alias="num_results", default=4)
    api_wrapper: DuckDuckGoSearchAPIWrapper = Field(...)
    backend: str = "text"
    args_schema: Type[BaseModel] = DDGInput
    keys_to_include: Optional[List[str]] = None
    results_separator: str = ", "
    output_format: Literal["string", "json", "list"] = "string"
    response_format: Literal["content_and_artifact"] = "content_and_artifact"

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> tuple[Union[List[dict], str], List[dict]]:
        """Use the tool."""
        raw_results = self.api_wrapper.results(query, self.max_results, source=self.backend)
        results = [
            {k: v for k, v in d.items() if not self.keys_to_include or k in self.keys_to_include}
            for d in raw_results
        ]

        if self.output_format == "list":
            return results, raw_results
        elif self.output_format == "json":
            return json.dumps(results), raw_results
        elif self.output_format == "string":
            res_strs = [", ".join([f"{k}: {v}" for k, v in d.items()]) for d in results]
            return self.results_separator.join(res_strs), raw_results
        else:
            raise ValueError(f"Invalid output_format: {self.output_format}")
```

**关键点**：
- 支持多种输出格式：`string`、`json`、`list`
- 使用 `response_format="content_and_artifact"` 返回元组
- 返回 `(formatted_results, raw_results)` 两部分
- 支持过滤结果字段 (`keys_to_include`)

### 4. DuckDuckGoSearchAPIWrapper - API 封装

```python
# duckduckgo_search.py:12-178
class DuckDuckGoSearchAPIWrapper(BaseModel):
    region: Optional[str] = "wt-wt"
    safesearch: str = "moderate"
    time: Optional[str] = "y"
    max_results: int = 5
    backend: str = "auto"
    source: str = "text"

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Any:
        """Validate that python package exists in environment."""
        try:
            from ddgs import DDGS
        except ImportError:
            raise ImportError("Could not import ddgs python package...")
        return values

    def run(self, query: str) -> str:
        """Run query through DuckDuckGo and return concatenated results."""
        if self.source == "text":
            results = self._ddgs_text(query)
        elif self.source == "news":
            results = self._ddgs_news(query)
        elif self.source == "images":
            results = self._ddgs_images(query)
        else:
            results = []

        if not results:
            return "No good DuckDuckGo Search Result was found"
        return " ".join(r["body"] for r in results)

    def results(self, query: str, max_results: int, source: Optional[str] = None) -> List[Dict[str, str]]:
        """Run query through DuckDuckGo and return metadata."""
        source = source or self.source
        if source == "text":
            results = [
                {"snippet": r["body"], "title": r["title"], "link": r["href"]}
                for r in self._ddgs_text(query, max_results=max_results)
            ]
        # ... news 和 images 的处理
        return results
```

**设计模式**：
- **Utility/Wrapper 模式**：将第三方 API 调用封装到独立的类中
- **环境验证**：使用 `@model_validator` 在实例化前检查依赖
- **多源支持**：支持 text、news、images 三种搜索源

## 两种实现方式对比

| 特性 | 继承 BaseTool (DuckDuckGo) | @tool 装饰器 (calculator) |
|------|---------------------------|--------------------------|
| 定义方式 | `class MyTool(BaseTool)` | `@tool def func(...)` |
| 代码量 | 较多（类定义） | 较少（函数定义） |
| 灵活性 | 高（可添加复杂配置） | 中等 |
| 适用场景 | 需要配置、状态管理 | 简单函数转换 |
| args_schema | 手动定义 Pydantic 模型 | 自动从函数签名生成 |
| name/description | 显式定义为类属性 | 从函数名/docstring 提取 |
| 依赖注入 | 通过 Field(default_factory=) | 通过闭包捕获 |

## 关键代码位置速查

| 组件 | 文件 | 行号 |
|------|------|------|
| `DDGInput` | `tool.py` | 14-17 |
| `DuckDuckGoSearchRun` | `tool.py` | 20-74 |
| `DuckDuckGoSearchResults` | `tool.py` | 77-135 |
| `DuckDuckGoSearchAPIWrapper` | `duckduckgo_search.py` | 12-178 |

## 总结

DuckDuckGo 搜索工具采用**继承 `BaseTool`** 的实现方式，这是一种更传统和灵活的模式：

1. **清晰的分层架构**：Tool（工具层）+ APIWrapper（API 封装层）+ 第三方库
2. **丰富的配置选项**：支持多种搜索源、输出格式、结果过滤
3. **环境验证**：通过 Pydantic 验证器确保依赖存在
4. **两种工具变体**：`DuckDuckGoSearchRun`（简单）和 `DuckDuckGoSearchResults`（高级）

相比之下，`@tool` 装饰器更适合快速创建简单工具，而继承 `BaseTool` 则更适合需要复杂配置和状态管理的场景。