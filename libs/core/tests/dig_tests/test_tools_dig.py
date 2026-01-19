"""Integration tests for LLM chat functionality.

These tests require network access and valid API credentials.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

# 配置 DeepSeek 的 API 信息
# API_KEY = "sk-tncozlnufknljijeakvlxhaebbunjjminzlxlmdknjqexbfm"  # 从 DeepSeek 控制台获取
# BASE_URL = "https://api.siliconflow.cn/v1/"  # DeepSeek 官方 API 端点
# MODEL_NAME = "Pro/deepseek-ai/DeepSeek-V3"

# 配置 GLM 的 API 信息
API_KEY = "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"
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "z-ai/glm4.7"


def add(a: int = 0, b: int = 0) -> int:
    return a + b


@tool(name_or_callable="万能计算器", parse_docstring=True)
def calculator(expression: str) -> str:
    """A simple calculator that evaluates basic mathematical expressions.

    Args:
        expression: A mathematical expression as a string (e.g., "2 + 2", "10 * 5").

    Returns:
        The result of the mathematical evaluation as a string.
    """
    try:
        # Safe evaluation of basic math expressions
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def test_tool_calling_with_calculator() -> None:
    """Test tool calling with a simple calculator tool.

    This test demonstrates:
    1. Defining a custom tool using the @tool decorator
    2. Binding tools to a chat model
    3. Invoking the model with tool calling capabilities
    """
    # Initialize the chat model with DeepSeek configuration
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL_NAME,
        temperature=0,
    )
    print("oh-my-lady-gaga")
    print(f"there is tools:{calculator.name}")
    # 4. 打印 `tool_name.name`，`tool_name.description` 和 `tool_name.args`。
    print(f"tool' is tools:{calculator.name}")
    print(f"tool_description :{calculator.description}")
    print(f"tool_args :{calculator.args}")
    print(f"tool_args :{calculator.response_format}")
    print("oh-my-lady-gaga")

    # add函数是没有加@tools注解的，所以也没有name,description,args等字段值
    # print(f"add' is tools:{add.name}")
    # print(f"add_description :{add.description}")
    # print(f"add_args :{add.args}")

    # Bind the calculator tool to the model
    # llm_with_tools = llm.bind_tools([calculator])

    # # Create a prompt that asks for a calculation
    # prompt = "What is 25 multiplied by 4 plus 17?"

    # # Invoke the model with the bound tools
    # response = llm_with_tools.invoke(prompt)

    # # The response should contain tool calls
    # print(f"Response: {response}")
    # print(f"Tool calls: {response.tool_calls}")

    # # Verify the model attempted to call the calculator
    # assert response.tool_calls is not None, "Model should make tool calls"

    # # Extract tool call arguments and execute the calculator
    # if response.tool_calls:
    #     tool_call = response.tool_calls[0]
    #     result = calculator.invoke(tool_call["args"])
    #     print(f"Calculation result: {result}")


if __name__ == "__main__":
    test_tool_calling_with_calculator()
