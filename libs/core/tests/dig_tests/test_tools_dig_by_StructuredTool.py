"""集成测试：使用 StructuredTool 创建工具并通过 LLM 调用。

这些测试需要网络访问和有效的 API 凭证。
"""
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool

# 配置 API 信息
API_KEY = "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"
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "z-ai/glm4.7"


def calculator(expression: str) -> str:
    """一个简单的计算器，用于计算基本数学表达式。

    Args:
        expression: 数学表达式字符串（例如 "2 + 2", "10 * 5"）。

    Returns:
        数学计算结果的字符串形式。
    """
    try:
        # 安全计算基本数学表达式
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"错误: {e}"


def test_structured_tool_with_calculator() -> None:
    """测试使用 StructuredTool 创建计算器工具并通过 LLM 调用。

    这个测试演示：
    1. 使用 StructuredTool.from_function() 创建自定义工具
    2. 将工具绑定到聊天模型
    3. 使用工具调用能力调用模型
    """
    # 使用 StructuredTool.from_function 创建计算器工具
    calculator_tool = StructuredTool.from_function(
        func=calculator,
        name="calculator",
        description="一个简单的计算器工具，可以执行基本的数学运算",
    )

    # 初始化聊天模型
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL_NAME,
        temperature=0,
    )

    print(f"工具名称: {calculator_tool.name}")
    print(f"工具描述: {calculator_tool.description}")
    print(f"工具参数: {calculator_tool.args}")

    # 将计算器工具绑定到模型
    llm_with_tools = llm.bind_tools([calculator_tool])

    # 创建一个需要计算的提示
    prompt = "25 乘以 4 再加上 17 等于多少？"

    # 调用带有绑定工具的模型
    response = llm_with_tools.invoke(prompt)

    # 打印响应
    print(f"响应: {response}")
    print(f"工具调用: {response.tool_calls}")

    # 验证模型尝试调用计算器
    assert response.tool_calls is not None, "模型应该调用工具"

    # 提取工具调用参数并执行计算器
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        result = calculator_tool.invoke(tool_call["args"])
        print(f"计算结果: {result}")


if __name__ == "__main__":
    test_structured_tool_with_calculator()
