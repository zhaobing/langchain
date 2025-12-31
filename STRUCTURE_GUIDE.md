# LangChain Monorepo 目录结构说明

## 📦 核心包说明

### libs/core/ - `langchain-core` ⭐ 研究重点
**这是你应该花最多时间研究的地方！**

```
libs/core/
├── langchain_core/
│   ├── prompts/              # 提示模板系统
│   │   ├── base.py           # BasePromptTemplate抽象类
│   │   ├── prompt.py         # PromptTemplate实现
│   │   ├── string.py         # StringPromptTemplate基类
│   │   ├── chat.py           # ChatPromptTemplate
│   │   └── image.py          # 图像提示模板
│   ├── runnables/            # 核心Runnable接口 ⭐⭐⭐
│   │   ├── base.py           # Runnable抽象基类
│   │   ├── config.py         # RunnableConfig
│   │   ├── passthrough.py    # RunnablePassthrough
│   │   ├── branch.py         # RunnableBranch
│   │   └── router.py         # RunnableLambda/RunnableBranch
│   ├── output_parsers/       # 输出解析器
│   │   ├── base.py           # BaseOutputParser
│   │   ├── pydantic.py       # PydanticOutputParser
│   │   └── json.py           # JSON输出解析
│   ├── tools/                # 工具抽象
│   │   ├── base.py           # BaseTool
│   │   └── structured.py     # StructuredTool
│   ├── messages/             # 消息格式
│   │   ├── base.py           # BaseMessage
│   │   ├── human.py          # HumanMessage
│   │   ├── ai.py             # AIMessage
│   │   └── system.py         # SystemMessage
│   └── language_models/      # LLM抽象
│       ├── llms.py           # BaseLLM
│       └── chat.py           # BaseChatModel
└── tests/                    # 单元测试（很好的学习资源）
```

**为什么从这里开始？**
- ✅ 最简洁、最核心的抽象
- ✅ 依赖最少，易于理解
- ✅ 所有其他包都基于此
- ✅ 代码质量高，文档完善

---

### libs/langchain_v1/ - `langchain` ⭐ 应用重点
**主力用户包，实际应用应该用这个**

```
libs/langchain_v1/
├── langchain/
│   ├── agents/               # Agent实现 ⭐⭐
│   │   ├── agent.py          # Agent抽象
│   │   ├── react.py          # ReAct Agent
│   │   └── tools.py          # Agent工具管理
│   ├── chains/               # Chain实现
│   │   ├── base.py           # Chain基类
│   │   ├── llm.py            # LLMChain
│   │   └── sequential/       # SequentialChain
│   ├── tools/                # 具体工具实现
│   │   ├── tool.py           # 工具装饰器
│   │   └── *
│   ├── retrieval/            # 检索相关
│   └── callbacks/            # 回调系统
└── tests/
```

**特点**：
- ✅ 完整的应用级功能
- ✅ 与LangGraph深度集成
- ✅ 适合构建生产应用
- ⚠️ 依赖较多，复杂度较高

---

### libs/langchain/ - `langchain-classic` ❌ 遗留代码
**不要在这个包上花时间！**

```
libs/langchain/
└── langchain_classic/        # 旧的实现，保持兼容
    ├── chains/               # 旧版Chain（已被langchain_v1替代）
    ├── agents/               # 旧版Agent
    ├── prompts/              # 从core重新导出
    └── *                     # 其他遗留功能
```

**为什么不要研究？**
- ❌ 不再添加新功能
- ❌ 维护模式
- ❌ 代码风格较旧
- ✅ 只用于保持旧项目兼容性

---

### libs/partners/ - 第三方集成
**按需研究**

```
libs/partners/
├── openai/                   # OpenAI集成
├── anthropic/                # Claude集成
├── ollama/                   # 本地模型
└── *                         # 其他集成
```

**建议**：使用时再看，不需要预先深入研究

---

## 🎯 推荐的学习路径

### 第1周：核心基础
```
libs/core/langchain_core/
├── messages/                 # 理解消息格式
│   └── base.py               # BaseMessage及其子类
├── prompts/                  # 理解提示系统
│   ├── string.py             # StringPromptTemplate
│   └── prompt.py             # PromptTemplate
└── runnables/
    └── base.py               # Runnable接口（核心概念）
```

### 第2周：Runnable体系
```
libs/core/langchain_core/runnables/
├── base.py                   # 深入理解Runnable
├── config.py                 # 理解配置和传递
├── passthrough.py            # 理解数据流
├── branch.py                 # 理解条件分支
└── router.py                 # 理解动态路由
```

### 第3-4周：工具和输出解析
```
libs/core/langchain_core/
├── tools/
│   ├── base.py               # 工具抽象
│   └── structured.py         # 结构化工具
└── output_parsers/
    ├── base.py               # 输出解析基类
    ├── pydantic.py           # Pydantic集成
    └── json.py               # JSON解析
```

### 第5-6周：应用层
```
libs/langchain_v1/langchain/
├── agents/
│   ├── agent.py              # Agent抽象
│   └── react.py              # ReAct实现
└── chains/
    └── base.py               # Chain实现
```

---

## 📖 如何阅读源码

### 1. 使用你创建的调试环境
你已经有了很好的调试环境：
```
libs/langchain/langchain_classic/01-dig/
├── 02_dig_prompt_template.py      # PromptTemplate示例
├── test_prompt_template.py        # PromptTemplate测试
└── README.md                      # 调试指南
```

### 2. 推荐的源码阅读工具
- **VSCode**: 配合你创建的launch.json调试配置
- **测试文件**: `tests/unit_tests/`是最好的使用示例
- **文档**: `libs/core/langchain_core/**/*.py` 中的docstring

### 3. 阅读顺序
```python
# 先看抽象接口
from langchain_core.prompts import BasePromptTemplate
from langchain_core.runnables import Runnable

# 再看具体实现
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

# 最后看应用层
from langchain.agents import AgentExecutor
```

---

## 🚫 常见误区

### ❌ 错误做法：
1. 直接研究 `libs/langchain/` (langchain-classic)
2. 试图一次性理解所有代码
3. 忽视测试文件
4. 从复杂的Agent开始

### ✅ 正确做法：
1. 从 `libs/core/` 开始
2. 逐层深入（基础→Runnable→工具→Agent）
3. 大量阅读测试用例
4. 从简单的PromptTemplate开始

---

## 📚 关键文件速查

| 概念 | 文件路径 | 重要性 |
|------|----------|--------|
| PromptTemplate | `libs/core/langchain_core/prompts/prompt.py` | ⭐⭐⭐ |
| Runnable接口 | `libs/core/langchain_core/runnables/base.py` | ⭐⭐⭐ |
| 消息格式 | `libs/core/langchain_core/messages/base.py` | ⭐⭐⭐ |
| 工具抽象 | `libs/core/langchain_core/tools/base.py` | ⭐⭐ |
| 输出解析 | `libs/core/langchain_core/output_parsers/base.py` | ⭐⭐ |
| Agent | `libs/langchain_v1/langchain/agents/agent.py` | ⭐⭐ |
| ReAct Agent | `libs/langchain_v1/langchain/agents/react.py` | ⭐ |

---

## 💡 实用建议

1. **先用再看**: 先使用API，再看源码
2. **测试驱动**: 从测试用例理解用法
3. **调试深入**: 用调试器跟踪执行流程
4. **文档对照**: 源码+官方文档结合
5. **记录笔记**: 建立自己的知识体系

---

## 🎓 扩展学习

完成以上内容后，可以继续研究：
- [LangGraph](https://github.com/langchain-ai/langgraph) - LangChain的底层编排框架
- [LangSmith](https://smith.langchain.com) - 调试和监控平台
- 具体集成（partners/目录下的各个包）

---

**Happy Learning! 🚀**

记住：**libs/core** 是你的朋友，**libs/langchain** 是主力，**libs/langchain_v1** 是应用层，**libs/langchain/** (langchain-classic) 是历史！
