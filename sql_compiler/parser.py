"""SQL语法分析器 - 负责根据Token序列构建抽象语法树(AST)"""

from typing import List, Optional

from .ast_nodes import (
    BinaryExpression,
    ColumnDef,
    CreateTableStatement,
    DataType,
    DeleteStatement,
    Expression,
    Identifier,
    InsertStatement,
    Literal,
    SelectStatement,
    SQLProgram,
    Statement,
    UpdateStatement,
)
from .lexer import SQLLexer, Token, TokenType


class ParseError(Exception):
    """语法分析错误"""

    def __init__(self, message: str, token: Token, expected: Optional[str] = None):
        self.message = message
        self.token = token
        self.expected = expected
        location = f"line {token.line}, column {token.column}"

        if expected:
            full_message = f"Parse error at {location}: {message}. Expected: {expected}, got: '{token.value}'"
        else:
            full_message = f"Parse error at {location}: {message}"

        super().__init__(full_message)


class SQLParser:
    """SQL语法分析器 - 采用递归下降分析方法"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else None

    def advance(self):
        """移动到下一个Token"""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = Token(TokenType.EOF, "", 0, 0)

    def peek(self, offset: int = 1) -> Optional[Token]:
        """预览后续Token"""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def match(self, *token_types: TokenType) -> bool:
        """检查当前Token是否匹配指定类型"""
        return self.current_token and self.current_token.type in token_types

    def consume(self, token_type: TokenType, error_message: str = "") -> Token:
        """消费指定类型的Token"""
        if not self.match(token_type):
            expected = token_type.name
            message = error_message or f"Expected {expected}"
            raise ParseError(message, self.current_token, expected)

        token = self.current_token
        self.advance()
        return token

    def parse(self) -> SQLProgram:
        """解析SQL程序"""
        statements = []

        while not self.match(TokenType.EOF):
            if self.current_token.type == TokenType.ERROR:
                raise ParseError(
                    f"Lexical error: {self.current_token.value}", self.current_token
                )

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

            # 可选的分号
            if self.match(TokenType.SEMICOLON):
                self.advance()

        return SQLProgram(statements, 1, 1)

    def parse_statement(self) -> Optional[Statement]:
        """解析SQL语句"""
        if not self.current_token:
            return None

        if self.match(TokenType.KEYWORD):
            keyword = self.current_token.value.upper()

            if keyword == "CREATE":
                return self.parse_create_table()
            elif keyword == "INSERT":
                return self.parse_insert()
            elif keyword == "SELECT":
                return self.parse_select()
            elif keyword == "DELETE":
                return self.parse_delete()
            elif keyword == "UPDATE":
                return self.parse_update()
            else:
                raise ParseError(
                    f"Unsupported statement: {keyword}", self.current_token
                )
        else:
            raise ParseError(
                "Expected statement",
                self.current_token,
                "CREATE, INSERT, SELECT, DELETE, or UPDATE",
            )

    def parse_create_table(self) -> CreateTableStatement:
        """解析CREATE TABLE语句"""
        line, column = self.current_token.line, self.current_token.column

        self.consume(TokenType.KEYWORD, "Expected CREATE")  # CREATE

        if (
            not self.match(TokenType.KEYWORD)
            or self.current_token.value.upper() != "TABLE"
        ):
            raise ParseError("Expected TABLE after CREATE", self.current_token, "TABLE")
        self.advance()  # TABLE

        # 表名
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value

        # 左括号
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after table name")

        # 列定义列表
        columns = []
        while not self.match(TokenType.RIGHT_PAREN):
            column = self.parse_column_definition()
            columns.append(column)

            if self.match(TokenType.COMMA):
                self.advance()
            elif not self.match(TokenType.RIGHT_PAREN):
                raise ParseError(
                    "Expected ',' or ')' in column list", self.current_token, ", or )"
                )

        if not columns:
            raise ParseError("Table must have at least one column", self.current_token)

        # 右括号
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after column list")

        return CreateTableStatement(table_name, columns, line, column)

    def parse_column_definition(self) -> ColumnDef:
        """解析列定义"""
        line, column = self.current_token.line, self.current_token.column

        # 列名
        column_name = self.consume(TokenType.IDENTIFIER, "Expected column name").value

        # 数据类型
        data_type = self.parse_data_type()

        return ColumnDef(column_name, data_type, line, column)

    def parse_data_type(self) -> DataType:
        """解析数据类型"""
        line, column = self.current_token.line, self.current_token.column

        if not self.match(TokenType.KEYWORD):
            raise ParseError(
                "Expected data type",
                self.current_token,
                "INT, INTEGER, VARCHAR, or CHAR",
            )

        type_name = self.current_token.value.upper()
        self.advance()

        # 处理带长度的类型，如VARCHAR(50)
        size = None
        if type_name in ["VARCHAR", "CHAR"] and self.match(TokenType.LEFT_PAREN):
            self.advance()  # (
            size_token = self.consume(TokenType.INTEGER, "Expected size after '('")
            size = int(size_token.value)
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after size")

        return DataType(type_name, size, line, column)

    def parse_insert(self) -> InsertStatement:
        """解析INSERT语句"""
        line, column = self.current_token.line, self.current_token.column

        self.consume(TokenType.KEYWORD, "Expected INSERT")  # INSERT

        if (
            not self.match(TokenType.KEYWORD)
            or self.current_token.value.upper() != "INTO"
        ):
            raise ParseError("Expected INTO after INSERT", self.current_token, "INTO")
        self.advance()  # INTO

        # 表名
        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value

        # 可选的列列表
        columns = None
        if self.match(TokenType.LEFT_PAREN):
            self.advance()  # (
            columns = []

            while not self.match(TokenType.RIGHT_PAREN):
                col_name = self.consume(
                    TokenType.IDENTIFIER, "Expected column name"
                ).value
                columns.append(col_name)

                if self.match(TokenType.COMMA):
                    self.advance()
                elif not self.match(TokenType.RIGHT_PAREN):
                    raise ParseError(
                        "Expected ',' or ')' in column list",
                        self.current_token,
                        ", or )",
                    )

            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after column list")

        # VALUES关键字
        if (
            not self.match(TokenType.KEYWORD)
            or self.current_token.value.upper() != "VALUES"
        ):
            raise ParseError("Expected VALUES", self.current_token, "VALUES")
        self.advance()  # VALUES

        # 值列表
        values = []
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after VALUES")

        current_row = []
        while not self.match(TokenType.RIGHT_PAREN):
            value = self.parse_literal()
            current_row.append(value)

            if self.match(TokenType.COMMA):
                self.advance()
            elif not self.match(TokenType.RIGHT_PAREN):
                raise ParseError(
                    "Expected ',' or ')' in value list", self.current_token, ", or )"
                )

        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after values")
        values.append(current_row)

        return InsertStatement(table_name, columns, values, line, column)

    def parse_select(self) -> SelectStatement:
        """解析SELECT语句"""
        line, column = self.current_token.line, self.current_token.column

        self.consume(TokenType.KEYWORD, "Expected SELECT")  # SELECT

        # 选择列表
        select_list = []
        while True:
            if self.match(TokenType.IDENTIFIER):
                col_name = self.current_token.value
                select_list.append(
                    Identifier(
                        col_name, self.current_token.line, self.current_token.column
                    )
                )
                self.advance()
            else:
                raise ParseError(
                    "Expected column name in SELECT list", self.current_token
                )

            if self.match(TokenType.COMMA):
                self.advance()
            else:
                break

        # FROM子句
        if (
            not self.match(TokenType.KEYWORD)
            or self.current_token.value.upper() != "FROM"
        ):
            raise ParseError("Expected FROM", self.current_token, "FROM")
        self.advance()  # FROM

        from_table = self.consume(
            TokenType.IDENTIFIER, "Expected table name after FROM"
        ).value

        # 可选的WHERE子句
        where_clause = None
        if (
            self.match(TokenType.KEYWORD)
            and self.current_token.value.upper() == "WHERE"
        ):
            self.advance()  # WHERE
            where_clause = self.parse_expression()

        return SelectStatement(select_list, from_table, where_clause, line, column)

    def parse_delete(self) -> DeleteStatement:
        """解析DELETE语句"""
        line, column = self.current_token.line, self.current_token.column

        self.consume(TokenType.KEYWORD, "Expected DELETE")  # DELETE

        if (
            not self.match(TokenType.KEYWORD)
            or self.current_token.value.upper() != "FROM"
        ):
            raise ParseError("Expected FROM after DELETE", self.current_token, "FROM")
        self.advance()  # FROM

        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value

        # 可选的WHERE子句
        where_clause = None
        if (
            self.match(TokenType.KEYWORD)
            and self.current_token.value.upper() == "WHERE"
        ):
            self.advance()  # WHERE
            where_clause = self.parse_expression()

        return DeleteStatement(table_name, where_clause, line, column)

    def parse_update(self) -> UpdateStatement:
        """解析UPDATE语句"""
        line, column = self.current_token.line, self.current_token.column

        self.consume(TokenType.KEYWORD, "Expected UPDATE")  # UPDATE

        table_name = self.consume(TokenType.IDENTIFIER, "Expected table name").value

        # SET子句
        if (
            not self.match(TokenType.KEYWORD)
            or self.current_token.value.upper() != "SET"
        ):
            raise ParseError("Expected SET after table name", self.current_token, "SET")
        self.advance()  # SET

        # 解析赋值列表 column=value, column=value, ...
        assignments = []
        while True:
            column_name = self.consume(
                TokenType.IDENTIFIER, "Expected column name"
            ).value
            self.consume(TokenType.EQUALS, "Expected '=' after column name")
            value = self.parse_primary()
            assignments.append((column_name, value))

            if self.match(TokenType.COMMA):
                self.advance()  # ,
            else:
                break

        # 可选的WHERE子句
        where_clause = None
        if (
            self.match(TokenType.KEYWORD)
            and self.current_token.value.upper() == "WHERE"
        ):
            self.advance()  # WHERE
            where_clause = self.parse_expression()

        return UpdateStatement(table_name, assignments, where_clause, line, column)

    def parse_expression(self) -> Expression:
        """解析表达式 - 简单的比较表达式"""
        return self.parse_comparison()

    def parse_comparison(self) -> Expression:
        """解析比较表达式"""
        left = self.parse_primary()

        if self.match(
            TokenType.EQUALS,
            TokenType.NOT_EQUALS,
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUALS,
            TokenType.GREATER_EQUALS,
        ):

            operator = self.current_token.value
            line, column = self.current_token.line, self.current_token.column
            self.advance()

            right = self.parse_primary()
            return BinaryExpression(left, operator, right, line, column)

        return left

    def parse_primary(self) -> Expression:
        """解析基本表达式"""
        if self.match(TokenType.IDENTIFIER):
            name = self.current_token.value
            line, column = self.current_token.line, self.current_token.column
            self.advance()
            return Identifier(name, line, column)

        elif self.match(TokenType.INTEGER, TokenType.STRING):
            return self.parse_literal()

        else:
            raise ParseError("Expected identifier or literal", self.current_token)

    def parse_literal(self) -> Literal:
        """解析字面量"""
        if self.match(TokenType.INTEGER):
            value = int(self.current_token.value)
            line, column = self.current_token.line, self.current_token.column
            self.advance()
            return Literal(value, "INT", line, column)

        elif self.match(TokenType.STRING):
            value = self.current_token.value
            line, column = self.current_token.line, self.current_token.column
            self.advance()
            return Literal(value, "STRING", line, column)

        else:
            raise ParseError("Expected literal value", self.current_token)


def main():
    """测试用例"""
    sql = """
    CREATE TABLE student(id INT, name VARCHAR(50), age INT);
    INSERT INTO student(id, name, age) VALUES (1, 'Alice', 20);
    SELECT id, name FROM student WHERE age > 18;
    DELETE FROM student WHERE id = 1;
    """

    print("输入SQL:")
    print(sql)
    print()

    try:
        # 词法分析
        lexer = SQLLexer(sql)
        tokens = lexer.tokenize()

        # 语法分析
        parser = SQLParser(tokens)
        ast = parser.parse()

        print("语法分析成功!")
        print("AST结构:")
        for i, stmt in enumerate(ast.statements):
            print(f"{i+1}. {stmt}")

    except Exception as e:
        print(f"分析错误: {e}")


if __name__ == "__main__":
    main()
