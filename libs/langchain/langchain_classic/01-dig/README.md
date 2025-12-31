# PromptTemplate 源码研究指南

本目录包含了用于深入研究 LangChain `PromptTemplate` 设计与实现的调试环境和示例代码。

## 📁 目录结构

```
01-dig/
├── 01_dig_simple_react.py        # ReAct Agent 示例（之前创建）
├── 02_dig_prompt_template.py      # PromptTemplate 调试示例（新）
├── test_prompt_template.py        # PromptTemplate 单元测试（新）
├── .env                           # 环境变量配置
└── README.md                      # 本文档
```

## 🎯 研究目标

通过可调试的示例和测试用例，深入理解：

1. **PromptTemplate 的核心实现机制**
   - 模板解析与变量提取
   - 变量替换与格式化
   - 部分变量填充（Partial Variables）

2. **不同模板格式的支持**
   - f-string（默认）
   - Jinja2
   - Mustache

3. **高级功能**
   - 模板组合（使用 `+` 运算符）
   - 模板验证
   - 从文件加载模板
   - 输入Schema生成

4. **设计模式与架构**
   - 继承层次结构
   - Pydantic 模型验证
   - 与 LangChain Runnable 接口的集成

## 🚀 快速开始

### 方法1: 使用VSCode调试器（推荐）

1. **打开文件**
   ```
   libs/langchain/langchain_classic/01-dig/02_dig_prompt_template.py
   ```

2. **设置断点**
   - 在代码中搜索 "断点设置位置" 的注释
   - 在这些行点击行号左侧设置断点
   - 推荐的第一个断点: `example_1_basic_template` 函数的第40行

3. **启动调试**
   - 按 `F5` 键
   - 或点击调试面板，选择 "Python: PromptTemplate - 基础调试"
   - 或使用命令面板 (`Cmd+Shift+P`) > "Debug: Start Debugging"

4. **调试操作**
   - `F10`: 单步跳过（Step Over）
   - `F11`: 单步进入（Step Into）
   - `Shift+F11`: 单步跳出（Step Out）
   - `F5`: 继续执行

5. **观察变量**
   - 左侧 "变量" 面板查看所有局部变量
   - 鼠标悬停在变量上查看其值
   - 在 "监视" 面板添加表达式进行监视

### 方法2: 运行测试用例

```bash
# 在项目根目录运行
cd /Users/zhaob/workspace/zhaob/zwk03/py-wk/langchain

# 方式1: 使用 pytest（推荐）
uv run --group test pytest libs/langchain/langchain_classic/01-dig/test_prompt_template.py -v -s

# 方式2: 使用 VSCode 调试器运行测试
# 按 F5 > 选择 "Python: PromptTemplate - 测试用例"

# 方式3: 直接运行
python libs/langchain/langchain_classic/01-dig/test_prompt_template.py
```

### 方法3: 直接运行示例

```bash
# 从项目根目录
cd /Users/zhaob/workspace/zhaob/zwk03/py-wk/langchain

# 使用 uv 运行
uv run python libs/langchain/langchain_classic/01-dig/02_dig_prompt_template.py

# 或使用 Python 直接运行
python libs/langchain/langchain_classic/01-dig/02_dig_prompt_template.py
```

## 📚 核心源码文件

### 主要类和文件

1. **PromptTemplate 类** - 主要研究对象
   ```
   libs/core/langchain_core/prompts/prompt.py
   ```
   - `from_template()` - 从字符串创建模板
   - `from_file()` - 从文件加载模板
   - `format()` - 格式化模板
   - `__add__()` - 模板组合

2. **StringPromptTemplate 基类**
   ```
   libs/core/langchain_core/prompts/string.py
   ```
   - 提供模板解析和格式化的基础功能
   - `get_template_variables()` - 提取模板变量
   - `check_valid_template()` - 验证模板
   - `DEFAULT_FORMATTER_MAPPING` - 不同格式的格式化器映射

3. **BasePromptTemplate 抽象基类**
   ```
   libs/core/langchain_core/prompts/base.py
   ```
   - 定义所有提示模板的通用接口
   - 继承自 `Runnable[Dict, PromptValue]`

4. **相关测试文件** - 了解最佳用法
   ```
   libs/core/tests/unit_tests/prompts/test_prompt.py
   ```

## 🔍 调试路线图

### 阶段1: 理解基础（30分钟）

**目标**: 理解 PromptTemplate 的基本工作流程

**步骤**:
1. 在 `example_1_basic_template()` 的第40行设置断点
2. 跟踪 `from_template()` 方法调用
3. 观察 `pre_init_validation()` 如何自动提取变量
4. 跟踪 `format()` 方法，查看字符串替换过程

**关键点**:
- `template_format` 默认是 "f-string"
- `input_variables` 自动从模板中提取
- `format()` 使用 Python 的字符串格式化

### 阶段2: 深入部分变量（20分钟）

**目标**: 理解 partial_variables 机制

**步骤**:
1. 在 `example_3_partial_variables()` 的第80行设置断点
2. 观察 `partial_variables` 参数如何影响 `input_variables`
3. 跟踪 `_merge_partial_and_user_variables()` 方法

**关键点**:
- partial 变量在创建时固定
- format 时只需提供剩余变量
- 用于预设固定的提示词部分（如系统指令）

### 阶段3: 探索模板组合（20分钟）

**目标**: 理解 `+` 运算符的实现

**步骤**:
1. 在 `example_5_template_combination()` 的第125行设置断点
2. F11 进入 `__add__()` 方法
3. 观察如何合并两个模板的变量和内容

**关键点**:
- 只能合并相同格式的模板
- 变量集合取并集
- partial_variables 也会合并

### 阶段4: 对比不同格式（30分钟）

**目标**: 理解 f-string vs Jinja2 vs Mustache

**步骤**:
1. 对比调试 `example_1_basic_template()` 和 `example_6_jinja2_template()`
2. 在 `string.py` 中查看 `DEFAULT_FORMATTER_MAPPING`
3. 跟踪不同格式的格式化函数

**关键点**:
- f-string: 使用 Python 内置字符串格式化
- Jinja2: 使用 `jinja2.SandboxedEnvironment`（安全考虑）
- Mustache: 使用 `chevron` 库

### 阶段5: 研究继承体系（40分钟）

**目标**: 理解类层次结构和设计模式

**类继承关系**:
```
Runnable (langchain_core/runnables/base.py)
  ↓
BasePromptTemplate (langchain_core/prompts/base.py)
  ↓
StringPromptTemplate (langchain_core/prompts/string.py)
  ↓
PromptTemplate (langchain_core/prompts/prompt.py)
```

**步骤**:
1. 查看每个类的职责
2. 理解模板方法模式的应用
3. 观察与 LangChain Runnable 体系的集成

## 🛠️ VSCode 调试配置

项目已配置好的调试配置（`.vscode/launch.json`）:

```json
{
  "name": "Python: PromptTemplate - 基础调试",
  "type": "debugpy",
  "request": "launch",
  "module": "langchain_classic.01-dig.02_dig_prompt_template",
  "justMyCode": false  // 可以进入库代码
}
```

**重要设置**:
- `"justMyCode": false` - 允许进入 LangChain 库代码
- `"env": {"PYTHONPATH": ...}` - 设置正确的 Python 路径

## 📝 调试技巧

### 1. 条件断点

右键点击断点 > "编辑断点" > 添加条件
```python
# 例如：只在特定变量值时暂停
name == "张三"
```

### 2. 日志点

不暂停代码，只输出消息
- 右键点击行号 > "添加日志点"
- 输入要输出的表达式，如:`当前变量: {name}`

### 3. 表达式求值

在调试时：
- 在 "调试控制台" 输入表达式求值
- 选中代码 > 右键 > "求值"

### 4. 调用堆栈

- 在 "调用堆栈" 面板查看函数调用链
- 双击可以跳转到不同的调用层次

## 🔧 常见问题

### Q1: 调试时无法进入 LangChain 源码

**A**: 确认 `launch.json` 中设置了 `"justMyCode": false`

### Q2: 找不到模块 langchain_core

**A**: 检查 `PYTHONPATH` 环境变量设置，确保包含了 `libs/core`

### Q3: 测试失败或报错

**A**: 确保在项目根目录运行，并且已安装依赖:
```bash
uv sync
```

## 📖 延伸阅读

### 相关文档
- [LangChain Prompts 文档](https://python.langchain.com/docs/concepts/#prompts)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [Python f-strings](https://docs.python.org/3/reference/lexical_analysis.html#f-strings)
- [Jinja2 模板文档](https://jinja.palletsprojects.com/)

### 相关源码
- `ChatPromptTemplate` - 聊天提示模板
- `MessagesPlaceholder` - 消息占位符
- `PipelinePromptTemplate` - 管道式提示模板

## 💡 研究建议

1. **循序渐进**: 按照调试路线图的顺序进行，不要跳过基础
2. **动手实践**: 修改示例代码，观察变化，加深理解
3. **记录笔记**: 在研究过程中记录关键发现
4. **对照文档**: 将源码行为与官方文档对照
5. **编写测试**: 为自己理解的功能编写测试用例

## 🤝 贡献

如果你发现了新的调试技巧或有改进建议，欢迎:
1. 更新本文档
2. 添加新的示例
3. 完善测试用例

## 📌 下一步研究方向

完成 PromptTemplate 研究后，可以继续研究:

1. **ChatPromptTemplate** - 聊天场景的提示模板
2. **FewShotPromptTemplate** - 少样本学习提示
3. **输出解析器 (Output Parsers)** - 如何结构化 LLM 输出
4. **Runnable 接口** - LangChain 的统一执行接口
5. **Chain 和 Agent** - 如何组合多个组件

---

**Happy Debugging! 🐛🔍**

如有问题，请查看 LangChain 官方文档或在项目仓库提 Issue。
