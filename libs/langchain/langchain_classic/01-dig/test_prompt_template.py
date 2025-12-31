#!/usr/bin/env python3
"""
PromptTemplate 单元测试
用于测试和验证 PromptTemplate 的各种功能

使用方法:
1. 在VSCode中按 F5 选择 "Python: PromptTemplate - 测试用例"
2. 或在命令行运行: pytest libs/langchain/langchain_classic/01-dig/test_prompt_template.py -v -s
"""

import pytest
from langchain_core.prompts import PromptTemplate
from datetime import datetime
import tempfile
import os


class TestPromptTemplateBasics:
    """测试 PromptTemplate 基础功能"""

    def test_from_template_single_variable(self):
        """测试: 单变量模板"""
        prompt = PromptTemplate.from_template("你好，{name}！")
        result = prompt.format(name="张三")

        assert result == "你好，张三！"
        assert "name" in prompt.input_variables

    def test_from_template_multiple_variables(self):
        """测试: 多变量模板"""
        prompt = PromptTemplate.from_template("{greeting}，{name}！")
        result = prompt.format(greeting="你好", name="李四")

        assert result == "你好，李四！"
        assert set(prompt.input_variables) == {"greeting", "name"}

    def test_format_with_missing_variable(self):
        """测试: 缺少变量时应该抛出异常"""
        prompt = PromptTemplate.from_template("你好，{name}！")

        with pytest.raises(KeyError):
            prompt.format()  # 缺少 name 参数

    def test_template_with_no_variables(self):
        """测试: 无变量的模板"""
        prompt = PromptTemplate.from_template("这是一个静态文本")
        result = prompt.format()

        assert result == "这是一个静态文本"
        assert len(prompt.input_variables) == 0


class TestPromptTemplatePartialVariables:
    """测试部分变量填充功能"""

    def test_partial_variables_basic(self):
        """测试: 基础的部分变量填充"""
        prompt = PromptTemplate.from_template(
            "{greeting}，{name}！",
            partial_variables={"greeting": "你好"}
        )

        # 只需填充剩余变量
        result = prompt.format(name="王五")
        assert result == "你好，王五！"

        # 验证 partial_variables 属性
        assert prompt.partial_variables == {"greeting": "你好"}
        assert prompt.input_variables == ["name"]

    def test_partial_variables_override(self):
        """测试: 部分变量不能被 format 覆盖"""
        prompt = PromptTemplate.from_template(
            "{greeting}，{name}！",
            partial_variables={"greeting": "你好"}
        )

        # 即使在 format 中提供 greeting，也应该使用 partial 的值
        result = prompt.format(name="王五", greeting="欢迎")
        # 注意: 这里的行为取决于具体实现，需要测试验证
        print(f"Result: {result}")

    def test_partial_multiple_variables(self):
        """测试: 多个部分变量"""
        prompt = PromptTemplate.from_template(
            "{a} + {b} + {c}",
            partial_variables={"a": "1", "b": "2"}
        )

        result = prompt.format(c="3")
        assert result == "1 + 2 + 3"


class TestPromptTemplateValidation:
    """测试模板验证功能"""

    def test_validation_success(self):
        """测试: 验证成功的案例"""
        prompt = PromptTemplate(
            template="你好，{name}！",
            input_variables=["name"],
            validate_template=True
        )
        assert "name" in prompt.input_variables

    def test_validation_mismatch(self):
        """测试: input_variables 与模板不匹配时应该失败"""
        with pytest.raises(ValueError):
            PromptTemplate(
                template="你好，{name}！",
                input_variables=["wrong_variable"],
                validate_template=True
            )

    def test_auto_detect_variables(self):
        """测试: 自动从模板检测变量"""
        prompt = PromptTemplate.from_template("{a} 和 {b} 和 {c}")
        assert set(prompt.input_variables) == {"a", "b", "c"}


class TestPromptTemplateCombination:
    """测试模板组合功能"""

    def test_add_two_prompts(self):
        """测试: 使用 + 运算符组合两个模板"""
        prompt1 = PromptTemplate.from_template("第一部分: {a}\n")
        prompt2 = PromptTemplate.from_template("第二部分: {b}")

        combined = prompt1 + prompt2

        assert set(combined.input_variables) == {"a", "b"}
        result = combined.format(a="值A", b="值B")
        assert "值A" in result
        assert "值B" in result

    def test_add_prompt_with_string(self):
        """测试: PromptTemplate + 字符串"""
        prompt = PromptTemplate.from_template("{var1}")
        combined = prompt + " - 静态文本"

        result = combined.format(var1="测试")
        assert "测试" in result
        assert "静态文本" in result

    def test_add_different_format_raises_error(self):
        """测试: 不同格式的模板不能相加"""
        prompt1 = PromptTemplate.from_template("{var}", template_format="f-string")
        prompt2 = PromptTemplate.from_template("{var}", template_format="jinja2")

        with pytest.raises(ValueError, match="Cannot add templates of different formats"):
            _ = prompt1 + prompt2


class TestPromptTemplateFormats:
    """测试不同的模板格式"""

    def test_fstring_format(self):
        """测试: f-string 格式（默认）"""
        prompt = PromptTemplate.from_template(
            "Hello {name}, you are {age} years old",
            template_format="f-string"
        )
        result = prompt.format(name="Alice", age=30)

        assert "Alice" in result
        assert "30" in result

    def test_jinja2_format_basic(self):
        """测试: Jinja2 格式基础用法"""
        prompt = PromptTemplate.from_template(
            "Hello {{ name }}!",
            template_format="jinja2"
        )
        result = prompt.format(name="Bob")

        assert "Bob" in result

    def test_jinja2_format_conditional(self):
        """测试: Jinja2 条件语句"""
        prompt = PromptTemplate.from_template(
            "{% if show %}Visible{% else %}Hidden{% endif %}",
            template_format="jinja2"
        )

        result1 = prompt.format(show=True)
        result2 = prompt.format(show=False)

        assert "Visible" in result1
        assert "Hidden" in result2

    def test_mustache_format(self):
        """测试: Mustache 格式"""
        prompt = PromptTemplate.from_template(
            "Hello {{name}}!",
            template_format="mustache"
        )
        result = prompt.format(name="Charlie")

        assert "Charlie" in result


class TestPromptTemplateFromFile:
    """测试从文件加载模板"""

    def test_from_file_basic(self):
        """测试: 从文件加载基础模板"""
        template_content = "测试内容: {var}"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(template_content)
            temp_file = f.name

        try:
            prompt = PromptTemplate.from_file(temp_file)
            result = prompt.format(var="成功")

            assert "成功" in result
            assert "var" in prompt.input_variables
        finally:
            os.unlink(temp_file)

    def test_from_file_with_encoding(self):
        """测试: 从文件加载并指定编码"""
        template_content = "中文测试: {content}"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(template_content)
            temp_file = f.name

        try:
            prompt = PromptTemplate.from_file(temp_file, encoding='utf-8')
            result = prompt.format(content="编码测试")

            assert "编码测试" in result
        finally:
            os.unlink(temp_file)


class TestPromptTemplateExamples:
    """测试 from_examples 方法"""

    def test_from_examples_basic(self):
        """测试: 从示例创建模板"""
        examples = [
            "问题: {q1} 答案: {a1}",
            "问题: {q2} 答案: {a2}"
        ]

        prompt = PromptTemplate.from_examples(
            examples=examples,
            suffix="\n问题: {question}",
            input_variables=["q1", "a1", "q2", "a2", "question"]
        )

        # 验证模板包含所有示例和后缀
        assert "问题: {q1}" in prompt.template
        assert "问题: {question}" in prompt.template

    def test_from_examples_with_prefix(self):
        """测试: from_examples 带前缀"""
        examples = ["示例1", "示例2"]
        prefix = "前言\n"
        suffix = "\n结尾: {end}"

        prompt = PromptTemplate.from_examples(
            examples=examples,
            suffix=suffix,
            input_variables=["end"],
            prefix=prefix
        )

        assert "前言" in prompt.template
        assert "示例1" in prompt.template
        assert "结尾" in prompt.template


class TestPromptTemplateInputSchema:
    """测试输入Schema功能"""

    def test_get_input_schema(self):
        """测试: 获取输入Schema"""
        prompt = PromptTemplate.from_template("{var1} {var2}")
        schema = prompt.get_input_schema()

        # 验证Schema包含正确的字段
        assert "var1" in schema.model_fields
        assert "var2" in schema.model_fields

    def test_schema_validation(self):
        """测试: 使用Schema验证输入"""
        prompt = PromptTemplate.from_template("{content}")

        schema = prompt.get_input_schema()
        validated = schema(content="测试内容")

        assert validated.content == "测试内容"

    def test_partial_variables_in_schema(self):
        """测试: partial_variables 不在 Schema 中"""
        prompt = PromptTemplate.from_template(
            "{full} {partial}",
            partial_variables={"partial": "固定值"}
        )

        schema = prompt.get_input_schema()

        # partial 变量不应该在 schema 中
        assert "partial" not in schema.model_fields
        # 但 full 应该在
        assert "full" in schema.model_fields


class TestPromptTemplateEdgeCases:
    """测试边界情况"""

    def test_empty_template(self):
        """测试: 空模板"""
        prompt = PromptTemplate.from_template("")
        result = prompt.format()

        assert result == ""

    def test_template_with_braces_only(self):
        """测试: 模板中只有大括号但不作为变量"""
        prompt = PromptTemplate.from_template("这是 {text} 不是变量")
        result = prompt.format(text="变量")

        assert result == "这是 变量 不是变量"

    def test_duplicate_variables(self):
        """测试: 模板中有重复变量"""
        prompt = PromptTemplate.from_template("{name} 说: {name} 在这里")
        result = prompt.format(name="Alice")

        assert result == "Alice 说: Alice 在这里"
        # input_variables 应该去重
        assert prompt.input_variables == ["name"]


if __name__ == "__main__":
    # 可以直接运行这个文件来执行测试
    pytest.main([__file__, "-v", "-s"])
