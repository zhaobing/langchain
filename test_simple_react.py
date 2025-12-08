#!/usr/bin/env python3
"""
简化的 ReAct Agent 测试用例
专注于展示工具调用的核心流程
"""

from typing import Any

from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from typing_extensions import override

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI


class SimpleAddTool(BaseTool):
    """简单的加法工具"""

    name: str = "add"
    description: str = "用于计算两个数的和。输入格式：'数字1,数字2'"

    @override
    def _run(self, numbers: str) -> str:
        """计算两个数的和"""
        try:
            a, b = numbers.split(',')
            result = float(a.strip()) + float(b.strip())
            return str(result)
        except Exception as e:
            return f"错误：{str(e)}"


def main():
    """运行简单的测试"""

    # 1. 创建工具
    tools = [SimpleAddTool()]

    # 2. 创建 ReAct 提示
    template = """你有以下工具：

{tools}

工具名称：{tool_names}

使用以下格式：
Question: 问题
Thought: 思考过程
Action: 工具名称
Action Input: 工具输入
Observation: 工具输出
... (可重复)
Thought: 知道答案了
Final Answer: 最终答案

开始！

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)

    # 3. 创建 agent
    # 注意：需要设置环境变量 OPENAI_API_KEY
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    agent = create_react_agent(llm, tools, prompt)

    # 4. 创建执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True  # 显示详细执行过程
    )

    # 5. 测试
    print("测试：计算 15 + 27 = ?")
    result = agent_executor.invoke({"input": "计算 15 加 27 等于多少？"})
    print("\n答案:", result["output"])


if __name__ == "__main__":
    # 设置环境变量（如果需要）
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("请设置环境变量 OPENAI_API_KEY")
        print("例如: export OPENAI_API_KEY='your-api-key-here'")
        exit(1)

    main()