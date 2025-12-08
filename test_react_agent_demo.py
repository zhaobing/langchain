#!/usr/bin/env python3
"""
演示 create_react_agent 如何调用工具的完整示例

这个示例展示了：
1. 如何创建自定义工具
2. 如何设置 ReAct Agent
3. Agent 如何思考和调用工具
4. 如何调试整个流程

运行前请确保安装依赖：
uv sync --group test
"""

from typing import Any, Dict, List

from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from typing_extensions import override

# 导入必要的模块
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI  # 需要设置 OPENAI_API_KEY


# 定义几个简单的工具用于演示
class CalculatorTool(BaseTool):
    """一个简单的计算器工具，可以进行基本的数学运算"""

    name: str = "calculator"
    description: str = "用于执行基本数学运算。输入应该是类似 '2 + 3' 或 '10 * 5' 的数学表达式。"

    @override
    def _run(self, expression: str) -> str:
        """执行数学表达式"""
        try:
            # 安全地评估数学表达式
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                return "错误：表达式包含不允许的字符"

            # 使用 eval 计算表达式（仅用于演示，生产环境应使用更安全的方法）
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"


class SearchTool(BaseTool):
    """一个模拟的搜索工具"""

    name: str = "search"
    description: str = "用于搜索信息。输入要搜索的关键词。"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # 模拟一个简单的知识库
        self.knowledge_base = {
            "python": "Python 是一种高级编程语言，由 Guido van Rossum 创建。",
            "langchain": "LangChain 是一个用于构建基于大型语言模型的应用程序的框架。",
            "react": "ReAct (Reasoning and Acting) 是一种让 AI 模型能够推理和行动的方法。",
            "openai": "OpenAI 是一家 AI 研究公司，创建了 GPT 系列模型。",
        }

    @override
    def _run(self, query: str) -> str:
        """搜索信息"""
        query_lower = query.lower()

        # 在知识库中搜索
        for key, value in self.knowledge_base.items():
            if key in query_lower:
                return value

        # 如果没找到，返回默认信息
        return f"抱歉，没有找到关于 '{query}' 的信息。"


class WeatherTool(BaseTool):
    """一个模拟的天气查询工具"""

    name: str = "weather"
    description: str = "查询指定城市的天气情况。输入城市名称。"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # 模拟天气数据
        self.weather_data = {
            "北京": "晴天，温度 25°C",
            "上海": "多云，温度 28°C",
            "广州": "阵雨，温度 30°C",
            "深圳": "晴天，温度 29°C",
            "杭州": "阴天，温度 26°C",
        }

    @override
    def _run(self, city: str) -> str:
        """查询天气"""
        if city in self.weather_data:
            return f"{city}的天气：{self.weather_data[city]}"
        else:
            return f"抱歉，没有 {city} 的天气信息。"


def create_react_prompt() -> PromptTemplate:
    """创建 ReAct 风格的提示模板"""

    template = """你是一个智能助手，可以使用以下工具来回答问题：

工具：
{tools}

工具名称：{tool_names}

请使用以下格式来回答问题：

Question: 用户的问题
Thought: 我应该如何回答这个问题？我应该使用什么工具吗？
Action: 工具的名称
Action Input: 工具的输入参数
Observation: 工具返回的结果
... (这个 Thought/Action/Action Input/Observation 可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 对用户问题的最终回答

开始！

Question: {input}
Thought:{agent_scratchpad}"""

    return PromptTemplate.from_template(template)


def main():
    """主函数：运行 ReAct Agent 示例"""

    print("=== ReAct Agent 工具调用演示 ===\n")

    # 1. 创建工具
    tools = [
        CalculatorTool(),
        SearchTool(),
        WeatherTool(),
    ]

    print("可用工具：")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    print()

    # 2. 创建提示模板
    prompt = create_react_prompt()

    # 3. 初始化 LLM
    # 注意：需要设置环境变量 OPENAI_API_KEY
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        verbose=True  # 启用详细输出以查看调用过程
    )

    # 4. 创建 ReAct agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
        verbose=True
    )

    # 5. 创建 AgentExecutor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # 显示详细的执行过程
        handle_parsing_errors=True,  # 处理解析错误
        max_iterations=5  # 最大迭代次数
    )

    # 6. 测试用例
    test_cases = [
        "计算 123 + 456 等于多少？",
        "什么是 Python？",
        "北京今天的天气怎么样？",
        "先告诉我什么是 LangChain，然后计算 50 * 30",
    ]

    # 运行测试用例
    for i, question in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试用例 {i}: {question}")
        print(f"{'='*50}")

        try:
            # 执行 agent
            response = agent_executor.invoke({"input": question})
            print(f"\n最终答案: {response['output']}")
        except Exception as e:
            print(f"\n错误: {str(e)}")

        print("\n" + "="*50 + "\n")
        print("等待下一个测试用例...\n")
        input("按回车键继续...")


def debug_single_step():
    """单步调试模式"""

    print("=== 单步调试模式 ===\n")

    # 创建工具和 agent（同上）
    tools = [CalculatorTool(), SearchTool()]
    prompt = create_react_prompt()
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, verbose=True)

    # 创建 agent 但不使用 AgentExecutor，手动执行每一步
    agent = create_react_agent(llm, tools, prompt)

    # 输入
    input_data = {
        "input": "计算 25 + 17 等于多少？",
        "intermediate_steps": []  # 存储中间步骤
    }

    print("输入:", input_data["input"])
    print("\n--- 执行第一步 ---")

    # 执行 agent
    result = agent.invoke(input_data)

    print("\n--- Agent 输出 ---")
    print(f"结果类型: {type(result)}")
    print(f"结果内容: {result}")

    # 如果是 AgentAction，说明需要调用工具
    if hasattr(result, 'tool'):
        print(f"\n--- 准备调用工具: {result.tool} ---")
        print(f"工具输入: {result.tool_input}")

        # 手动调用工具
        for tool in tools:
            if tool.name == result.tool:
                observation = tool.invoke(result.tool_input)
                print(f"工具输出: {observation}")

                # 将步骤添加到 intermediate_steps
                input_data["intermediate_steps"].append((result, observation))

                # 再次调用 agent
                print("\n--- 执行第二步 ---")
                result2 = agent.invoke(input_data)
                print(f"\n最终结果: {result2}")


if __name__ == "__main__":
    print("选择运行模式：")
    print("1. 完整演示模式")
    print("2. 单步调试模式")

    choice = input("请选择 (1 或 2): ").strip()

    if choice == "2":
        debug_single_step()
    else:
        main()