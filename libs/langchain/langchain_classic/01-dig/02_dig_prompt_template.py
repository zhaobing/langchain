#!/usr/bin/env python3
"""
PromptTemplate 深度调试示例
用于研究 PromptTemplate 的设计与实现

使用方法:
1. 在VSCode中按 F5 或使用调试面板选择 "Python: PromptTemplate - 基础调试"
2. 设置断点在感兴趣的地方（如 format 方法）
3. 单步执行，观察变量变化和函数调用链
"""

from langchain_core.prompts import PromptTemplate


def example_1_basic_template():
    """示例1: 最基础的模板使用"""
    print("\n" + "="*60)
    print("示例1: 基础模板使用")
    print("="*60)

    # 断点设置位置 1: 观察 from_template 的实现
    prompt = PromptTemplate.from_template("你好，{name}！")

    # 断点设置位置 2: 观察 format 如何替换变量
    result = prompt.format(name="张三")

    print(f"模板: {prompt.template}")
    print(f"输入变量: {prompt.input_variables}")
    print(f"格式化结果: {result}")
    return result


def example_2_multiple_variables():
    """示例2: 多变量模板"""
    print("\n" + "="*60)
    print("示例2: 多变量模板")
    print("="*60)

    template = """请回答以下问题：

问题: {question}
上下文: {context}
要求: {requirement}

请给出详细的答案。"""

    # 断点设置位置: 观察多变量如何解析
    prompt = PromptTemplate.from_template(template)

    print(f"检测到的变量: {prompt.input_variables}")

    result = prompt.format(
        question="什么是LangChain？",
        context="LangChain是一个用于开发LLM应用的框架",
        requirement="用一句话概括"
    )

    print(f"\n格式化结果:\n{result}")
    return result


def example_3_partial_variables():
    """示例3: 部分变量填充 (Partial Variables)"""
    print("\n" + "="*60)
    print("示例3: 部分变量填充")
    print("="*60)

    # 基础模板
    template = """
系统指令: {system_instruction}
用户问题: {user_question}
"""

    # 断点设置位置: 观察 partial_variables 如何工作
    prompt = PromptTemplate.from_template(
        template,
        partial_variables={
            "system_instruction": "你是一个友好的AI助手，请用简洁的语言回答问题。"
        }
    )

    print(f"全部输入变量: {prompt.input_variables}")
    print(f"部分变量: {prompt.partial_variables}")
    print(f"剩余需要填充的变量: {prompt.input_variables}")

    # 只需要填充剩余变量
    result = prompt.format(user_question="什么是Python？")
    print(f"\n格式化结果:{result}")
    return result


def example_4_template_validation():
    """示例4: 模板验证"""
    print("\n" + "="*60)
    print("示例4: 模板验证")
    print("="*60)

    # 断点设置位置: 观察验证逻辑
    try:
        prompt = PromptTemplate(
            template="你好，{name}！",
            input_variables=["name"],
            validate_template=True  # 启用验证
        )
        print("✓ 模板验证通过")
        print(f"变量: {prompt.input_variables}")
    except ValueError as e:
        print(f"✗ 验证失败: {e}")

    # 尝试创建不匹配的模板
    try:
        prompt = PromptTemplate(
            template="你好，{name}！",
            input_variables=["wrong_var"],  # 错误的变量名
            validate_template=True
        )
        print("✗ 不应该到达这里")
    except ValueError as e:
        print(f"✓ 预期的验证错误: {e}")


def example_5_template_combination():
    """示例5: 模板组合（使用 + 运算符）"""
    print("\n" + "="*60)
    print("示例5: 模板组合")
    print("="*60)

    prompt1 = PromptTemplate.from_template("第一部分: {var1}\n")
    prompt2 = PromptTemplate.from_template("第二部分: {var2}\n")

    # 断点设置位置: 观察 __add__ 方法实现
    combined = prompt1 + prompt2

    print(f"组合后的模板: {combined.template}")
    print(f"组合后的变量: {combined.input_variables}")

    result = combined.format(var1="值1", var2="值2")
    print(f"\n组合格式化结果:\n{result}")
    return result


def example_6_jinja2_template():
    """示例6: Jinja2 模板格式"""
    print("\n" + "="*60)
    print("示例6: Jinja2 模板格式")
    print("="*60)

    template = """
{% if show_greeting %}
你好，{{ name }}！
{% endif %}
你的年龄是 {{ age }} 岁。
{% if age >= 18 %}
你已经是成年人了。
{% else %}
你还未成年。
{% endif %}
"""

    # 断点设置位置: 观察 Jinja2 渲染逻辑
    prompt = PromptTemplate.from_template(
        template,
        template_format="jinja2"
    )

    result = prompt.format(name="李四", age=20, show_greeting=True)
    print(f"Jinja2格式化结果:\n{result}")
    return result


def example_7_from_file():
    """示例7: 从文件加载模板"""
    print("\n" + "="*60)
    print("示例7: 从文件加载模板")
    print("="*60)

    # 首先创建一个示例模板文件
    import tempfile
    import os

    template_content = """# 智能助手对话历史

用户: {user_input}
助手: {assistant_response}

时间: {timestamp}
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(template_content)
        temp_file = f.name

    try:
        # 断点设置位置: 观察文件加载逻辑
        prompt = PromptTemplate.from_file(temp_file)

        print(f"从文件加载的模板: {prompt.template}")
        print(f"检测到的变量: {prompt.input_variables}")

        from datetime import datetime
        result = prompt.format(
            user_input="你好",
            assistant_response="你好！有什么我可以帮助你的吗？",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        print(f"\n格式化结果:\n{result}")
        return result
    finally:
        os.unlink(temp_file)


def example_8_input_schema():
    """示例8: 输入Schema（用于验证）"""
    print("\n" + "="*60)
    print("示例8: 输入Schema")
    print("="*60)

    prompt = PromptTemplate.from_template(
        "请处理以下内容: {content}，使用选项: {option}"
    )

    # 断点设置位置: 观察 Schema 生成
    schema = prompt.get_input_schema()

    print(f"Schema类: {schema.__name__}")
    print(f"Schema字段: {schema.model_fields.keys()}")

    # 使用 Schema 验证输入
    try:
        validated_input = schema(content="测试内容", option="A")
        print(f"✓ 验证通过: {validated_input}")
    except Exception as e:
        print(f"✗ 验证失败: {e}")


def main():
    """运行所有示例"""
    print("\n" + "#"*60)
    print("# PromptTemplate 源码调试")
    print("#"*60)
    print("\n提示: 在代码中标记了 '断点设置位置' 的地方设置断点")
    print("然后按 F5 开始调试，观察代码执行流程\n")

    # 运行各个示例
    example_1_basic_template()
    example_2_multiple_variables()
    example_3_partial_variables()
    example_4_template_validation()
    example_5_template_combination()
    example_6_jinja2_template()
    example_7_from_file()
    example_8_input_schema()

    print("\n" + "#"*60)
    print("# 调试完成")
    print("#"*60)
    print("\n推荐的调试顺序:")
    print("1. 先调试 example_1，理解基础的 from_template 和 format")
    print("2. 然后调试 example_3，理解 partial_variables 的机制")
    print("3. 再调试 example_5，理解模板组合")
    print("4. 最后调试 example_6，对比不同模板格式的实现")
    print("\n关键源码文件:")
    print("- libs/core/langchain_core/prompts/prompt.py (PromptTemplate类)")
    print("- libs/core/langchain_core/prompts/string.py (StringPromptTemplate基类)")


if __name__ == "__main__":
    main()
