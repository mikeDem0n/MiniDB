"""SQL词法分析器 - 负责将SQL语句分解为Token序列"""

from enum import Enum, auto
from typing import List, Optional
from dataclasses import dataclass


class TokenType(Enum):
    """Token类型枚举"""
    # 关键字
    KEYWORD = auto()
    
    # 标识符和常量
    IDENTIFIER = auto()
    INTEGER = auto()
    STRING = auto()
    
    # 运算符
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUALS = auto()
    GREATER_EQUALS = auto()
    
    # 分隔符
    COMMA = auto()
    SEMICOLON = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    
    # 特殊
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """Token数据结构"""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"


class LexerError(Exception):
    """词法分析错误"""
    
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Lexical error at line {line}, column {column}: {message}")


class SQLLexer:
    """SQL词法分析器"""
    
    # SQL关键字
    KEYWORDS = {
        'CREATE', 'TABLE', 'INSERT', 'INTO', 'SELECT', 'FROM', 'WHERE',
        'VALUES', 'DELETE', 'INT', 'INTEGER', 'VARCHAR', 'CHAR', 'AND', 'OR', 'NOT'
    }
    
    # 运算符映射
    OPERATORS = {
        '=': TokenType.EQUALS,
        '!=': TokenType.NOT_EQUALS,
        '<>': TokenType.NOT_EQUALS,
        '<': TokenType.LESS_THAN,
        '>': TokenType.GREATER_THAN,
        '<=': TokenType.LESS_EQUALS,
        '>=': TokenType.GREATER_EQUALS,
    }
    
    # 分隔符映射
    DELIMITERS = {
        ',': TokenType.COMMA,
        ';': TokenType.SEMICOLON,
        '(': TokenType.LEFT_PAREN,
        ')': TokenType.RIGHT_PAREN,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def current_char(self) -> Optional[str]:
        """获取当前字符"""
        if self.position >= len(self.source):
            return None
        return self.source[self.position]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """预览后续字符"""
        pos = self.position + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """移动到下一个字符"""
        if self.position >= len(self.source):
            return None
        
        char = self.source[self.position]
        self.position += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char() and self.current_char().isspace():
            self.advance()
    
    def read_string(self) -> str:
        """读取字符串字面量"""
        quote_char = self.current_char()  # ' 或 "
        start_line, start_column = self.line, self.column
        self.advance()  # 跳过开始引号
        
        value = ""
        while self.current_char() and self.current_char() != quote_char:
            char = self.advance()
            if char == '\\':  # 处理转义字符
                next_char = self.advance()
                if next_char == 'n':
                    value += '\n'
                elif next_char == 't':
                    value += '\t'
                elif next_char == 'r':
                    value += '\r'
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote_char:
                    value += quote_char
                else:
                    value += next_char or ""
            else:
                value += char
        
        if not self.current_char():
            raise LexerError("Unterminated string literal", start_line, start_column)
        
        self.advance()  # 跳过结束引号
        return value
    
    def read_number(self) -> str:
        """读取数字"""
        value = ""
        while self.current_char() and self.current_char().isdigit():
            value += self.advance()
        return value
    
    def read_identifier(self) -> str:
        """读取标识符"""
        value = ""
        while (self.current_char() and 
               (self.current_char().isalnum() or self.current_char() == '_')):
            value += self.advance()
        return value
    
    def read_operator(self) -> str:
        """读取运算符"""
        char = self.current_char()
        
        # 检查双字符运算符
        if char in ['!', '<', '>']:
            next_char = self.peek_char()
            if next_char == '=':
                self.advance()  # 第一个字符
                self.advance()  # 第二个字符
                return char + '='
            elif char == '<' and next_char == '>':
                self.advance()
                self.advance()
                return '<>'
        
        # 单字符运算符
        return self.advance()
    
    def tokenize(self) -> List[Token]:
        """执行词法分析，返回Token列表"""
        self.tokens = []
        
        try:
            while self.position < len(self.source):
                self.skip_whitespace()
                
                if not self.current_char():
                    break
                
                char = self.current_char()
                current_line, current_column = self.line, self.column
                
                # 字符串字面量
                if char in ['"', "'"]:
                    try:
                        value = self.read_string()
                        token = Token(TokenType.STRING, value, 
                                    current_line, current_column)
                        self.tokens.append(token)
                    except LexerError as lex_error:
                        error_token = Token(TokenType.ERROR, lex_error.message, 
                                          current_line, current_column)
                        self.tokens.append(error_token)
                        raise
                
                # 数字
                elif char.isdigit():
                    value = self.read_number()
                    token = Token(TokenType.INTEGER, value, current_line, current_column)
                    self.tokens.append(token)
                
                # 标识符或关键字
                elif char.isalpha() or char == '_':
                    value = self.read_identifier()
                    token_type = (TokenType.KEYWORD if value.upper() in self.KEYWORDS 
                                 else TokenType.IDENTIFIER)
                    token = Token(token_type, value.upper(), current_line, current_column)
                    self.tokens.append(token)
                
                # 运算符
                elif char in '=!<>':
                    operator = self.read_operator()
                    if operator in self.OPERATORS:
                        token_type = self.OPERATORS[operator]
                        token = Token(token_type, operator, current_line, current_column)
                        self.tokens.append(token)
                    else:
                        raise LexerError(f"Unknown operator '{operator}'", current_line, current_column)
                
                # 分隔符
                elif char in self.DELIMITERS:
                    token_type = self.DELIMITERS[char]
                    token = Token(token_type, char, current_line, current_column)
                    self.tokens.append(token)
                    self.advance()
                
                # 单行注释
                elif char == '-' and self.peek_char() == '-':
                    # 跳过注释直到行末
                    while self.current_char() and self.current_char() != '\n':
                        self.advance()
                
                # 多行注释
                elif char == '/' and self.peek_char() == '*':
                    self.advance()  # 跳过 /
                    self.advance()  # 跳过 *
                    # 查找注释结束
                    while self.current_char():
                        if self.current_char() == '*' and self.peek_char() == '/':
                            self.advance()  # 跳过 *
                            self.advance()  # 跳过 /
                            break
                        self.advance()
                    else:
                        raise LexerError("Unterminated comment", current_line, current_column)
                
                # 未识别字符
                else:
                    raise LexerError(f"Unexpected character '{char}'", current_line, current_column)
            
            # 添加EOF标记
            self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
            
        except LexerError as e:
            # 添加错误Token
            error_token = Token(TokenType.ERROR, e.message, e.line, e.column)
            self.tokens.append(error_token)
            raise
        
        return self.tokens
    
    def get_tokens(self) -> List[Token]:
        """获取Token列表"""
        if not self.tokens:
            self.tokenize()
        return self.tokens
    
    def print_tokens(self):
        """打印Token序列，用于调试"""
        tokens = self.get_tokens()
        print("Token序列:")
        print("=" * 50)
        print(f"{'类型':<12} {'值':<15} {'位置':<10}")
        print("-" * 50)
        
        for token in tokens:
            if token.type == TokenType.EOF:
                break
            print(f"{token.type.name:<12} {token.value:<15} {token.line}:{token.column}")
        
        print("-" * 50)
        print(f"共生成 {len([t for t in tokens if t.type != TokenType.EOF])} 个Token")


def main():
    """测试用例"""
    sql = """
    CREATE TABLE student(
        id INT,
        name VARCHAR(50),
        age INT
    );
    
    INSERT INTO student(id, name, age) VALUES (1, 'Alice', 20);
    INSERT INTO student VALUES (2, "Bob", 22);
    
    SELECT id, name FROM student WHERE age > 18;
    
    DELETE FROM student WHERE id = 1;
    """
    
    print("输入SQL:")
    print(sql)
    print()
    
    try:
        lexer = SQLLexer(sql)
        lexer.print_tokens()
    except LexerError as e:
        print(f"词法分析错误: {e}")


if __name__ == "__main__":
    main()
