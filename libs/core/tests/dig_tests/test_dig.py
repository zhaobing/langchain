"""Integration tests for LLM chat functionality.

These tests require network access and valid API credentials.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessageChunk, HumanMessage

# 配置 DeepSeek 的 API 信息
DEEPSEEK_API_KEY = "sk-tncozlnufknljijeakvlxhaebbunjjminzlxlmdknjqexbfm"  # 从 DeepSeek 控制台获取
DEEPSEEK_BASE_URL = "https://api.siliconflow.cn/v1/"  # DeepSeek 官方 API 端点
DEEPSEEK_MODEL_NAME = "Pro/deepseek-ai/DeepSeek-V3"


def test_human_message_with_llm() -> None:

    llm = ChatOpenAI(
        model=DEEPSEEK_MODEL_NAME,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.7,
    )

    message = HumanMessage(content="你好，15字以内介绍你自己")
    print("即将开始发送消息")
    response = llm.invoke([message])

    print(f"\nLLM Response: {response.content}")

    assert message.content == "你好，15字以内介绍你自己"
    assert isinstance(message.content, str)


def test_streaming_with_message_chunks() -> None:
    """Test streaming to understand BaseMessageChunk usage.

    This test demonstrates:
    1. When BaseMessageChunk is used (streaming mode)
    2. How chunks are yielded incrementally
    3. How chunks are merged into a complete message
    """
    llm = ChatOpenAI(
        model=DEEPSEEK_MODEL_NAME,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.7,
    )

    message = HumanMessage(content="用20字介绍一下LangChain是什么")

    print("\n" + "=" * 60)
    print("STREAMING MODE - BaseMessageChunk 演示")
    print("=" * 60)
    print("\n使用 stream() 方法时，LLM 会返回 AIMessageChunk 对象：")
    print("- AIMessageChunk 继承自 BaseMessageChunk")
    print("- 每个chunk包含部分响应内容")
    print("- 可以通过 + 操作符合并多个chunk")
    print("\n" + "-" * 60)

    # 使用 stream 方法，会返回 AIMessageChunk (BaseMessageChunk的子类)
    full_response: AIMessageChunk | None = None
    chunk_count = 0

    for chunk in llm.stream([message]):
        chunk_count += 1
        print(f"\n[Chunk {chunk_count}]")
        print(f"  类型: {type(chunk).__name__}")  # AIMessageChunk
        print(f"  是否为 BaseMessageChunk 实例: {isinstance(chunk, AIMessageChunk)}")
        print(f"  内容片段: '{chunk.content}'")

        # 演示 chunk 的合并
        if full_response is None:
            full_response = chunk
        else:
            # BaseMessageChunk 实现了 __add__ 方法，可以合并
            full_response += chunk
            print(f"  累积内容: '{full_response.content}'")

    print("\n" + "-" * 60)
    print(f"\n总计收到 {chunk_count} 个 chunks")
    print(f"最终完整响应: {full_response.content if full_response else 'None'}")
    print("=" * 60)


def test_chunk_manipulation() -> None:
    """Test BaseMessageChunk concatenation behavior.

    演示 BaseMessageChunk 的核心功能：
    1. Chunk 可以通过 + 操作符合并
    2. 合并时 content 会拼接
    3. additional_kwargs 和 response_metadata 也会合并
    """
    from langchain_core.messages import AIMessageChunk

    print("\n" + "=" * 60)
    print("BaseMessageChunk 合并演示")
    print("=" * 60)

    # 创建三个 chunks
    chunk1 = AIMessageChunk(
        content="我是",
        id="msg-001",
    )
    chunk2 = AIMessageChunk(
        content="一个",
        id="msg-001",
    )
    chunk3 = AIMessageChunk(
        content="AI助手",
        id="msg-001",
    )

    print("\n初始 Chunks:")
    print(f"  Chunk 1: '{chunk1.content}'")
    print(f"  Chunk 2: '{chunk2.content}'")
    print(f"  Chunk 3: '{chunk3.content}'")

    # 逐个合并
    merged = chunk1 + chunk2 + chunk3

    print(f"\n合并后:")
    print(f"  完整内容: '{merged.content}'")
    print(f"  类型: {type(merged).__name__}")
    print(f"  ID: {merged.id}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Run the test directly
    # print("Test 1: 基本 invoke 调用")
    # test_human_message_with_llm()

    print("\n\nTest 2: Streaming 和 BaseMessageChunk")
    test_streaming_with_message_chunks()

    # print("\n\nTest 3: Chunk 合并操作")
    # test_chunk_manipulation()

    # print("\n\n✨ All tests completed!")
