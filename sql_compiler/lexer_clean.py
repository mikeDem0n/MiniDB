"""简化版SQL词法分析器 - 修复代码质量问题"""

from enum import Enum, auto
from typing import List, Optional
from dataclasses import dataclass


class TokenType(Enum):
    """Token类型枚举"""
    KEYWORD = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    STRING = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUALS = auto()
    GREATER_EQUALS = auto()
    COMMA = auto()
    SEMICOLON = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """Token数据结构"""
    type: TokenType
    value: str
    line: int
    column: int


class LexerError(Exception):
    """词法分析错误"""
    
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        location = f"line {line}, column {column}"
        super().__init__(f"Lexical error at {location}: {message}")


class SQLLexer:
    """SQL词法分析器"""
    
    KEYWORDS = {
        'CREATE', 'TABLE', 'INSERT', 'INTO', 'SELECT', 'FROM', 'WHERE',
        'VALUES', 'DELETE', 'INT', 'INTEGER', 'VARCHAR', 'CHAR'
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
        quote_char = self.current_char()
        start_line, start_column = self.line, self.column
        self.advance()
        
        value = ""
        while self.current_char() and self.current_char() != quote_char:
            char = self.advance()
            if char == '\\':
                next_char = self.advance()
                if next_char == 'n':
                    value += '\n'
                elif next_char == 't':
                    value += '\t'
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote_char:
                    value += quote_char
                else:
                    value += next_char or ""
            else:
                value += char
        
        if not self.current_char():
            raise LexerError("Unterminated string literal", 
                           start_line, start_column)
        
        self.advance()
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
    
    def tokenize(self) -> List[Token]:
        """执行词法分析"""
        self.tokens = []
        
        while self.position < len(self.source):
            self._process_next_token()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens
    
    def _process_next_token(self):
        """处理下一个Token"""
        self.skip_whitespace()
        
        if not self.current_char():
            return
        
        char = self.current_char()
        current_line, current_column = self.line, self.column
        
        try:
            if char in ['"', "'"]:
                self._process_string_token(current_line, current_column)
            elif char.isdigit():
                self._process_number_token(current_line, current_column)
            elif char.isalpha() or char == '_':
                self._process_identifier_token(current_line, current_column)
            elif char in '=!<>':
                self._process_operator_token(current_line, current_column)
            elif char in ',;()':
                self._process_delimiter_token(current_line, current_column)
            elif char == '-' and self._peek() == '-':
                self._skip_line_comment()
            else:
                raise LexerError(f"Unexpected character '{char}'", 
                               current_line, current_column)
        except LexerError as e:
            error_token = Token(TokenType.ERROR, e.message, 
                              current_line, current_column)
            self.tokens.append(error_token)
            raise
    
    def _process_string_token(self, line: int, column: int):
        """处理字符串Token"""
        value = self.read_string()
        token = Token(TokenType.STRING, value, line, column)
        self.tokens.append(token)
    
    def _process_number_token(self, line: int, column: int):
        """处理数字Token"""
        value = self.read_number()
        token = Token(TokenType.INTEGER, value, line, column)
        self.tokens.append(token)
    
    def _process_identifier_token(self, line: int, column: int):
        """处理标识符Token"""
        value = self.read_identifier()
        token_type = (TokenType.KEYWORD if value.upper() in self.KEYWORDS
                     else TokenType.IDENTIFIER)
        token = Token(token_type, value.upper(), line, column)
        self.tokens.append(token)
    
    def _process_operator_token(self, line: int, column: int):
        """处理运算符Token"""
        operator = self._read_operator()
        token_type = self._get_operator_type(operator)
        if token_type:
            token = Token(token_type, operator, line, column)
            self.tokens.append(token)
        else:
            raise LexerError(f"Unknown operator '{operator}'", line, column)
    
    def _process_delimiter_token(self, line: int, column: int):
        """处理分隔符Token"""
        char = self.advance()
        token_type = self._get_delimiter_type(char)
        if token_type:
            token = Token(token_type, char, line, column)
            self.tokens.append(token)
    
    def _skip_line_comment(self):
        """跳过单行注释"""
        while self.current_char() and self.current_char() != '\n':
            self.advance()
    
    def _peek(self, offset: int = 1) -> Optional[str]:
        """预览字符"""
        pos = self.position + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def _read_operator(self) -> str:
        """读取运算符"""
        char = self.current_char()
        
        if char in ['!', '<', '>'] and self._peek() == '=':
            self.advance()
            self.advance()
            return char + '='
        elif char == '<' and self._peek() == '>':
            self.advance()
            self.advance()
            return '<>'
        else:
            return self.advance()
    
    def _get_operator_type(self, operator: str) -> Optional[TokenType]:
        """获取运算符类型"""
        mapping = {
            '=': TokenType.EQUALS,
            '!=': TokenType.NOT_EQUALS,
            '<>': TokenType.NOT_EQUALS,
            '<': TokenType.LESS_THAN,
            '>': TokenType.GREATER_THAN,
            '<=': TokenType.LESS_EQUALS,
            '>=': TokenType.GREATER_EQUALS,
        }
        return mapping.get(operator)
    
    def _get_delimiter_type(self, delimiter: str) -> Optional[TokenType]:
        """获取分隔符类型"""
        mapping = {
            ',': TokenType.COMMA,
            ';': TokenType.SEMICOLON,
            '(': TokenType.LEFT_PAREN,
            ')': TokenType.RIGHT_PAREN,
        }
        return mapping.get(delimiter)
    
    def print_tokens(self):
        """打印Token序列"""
        if not self.tokens:
            self.tokenize()
        
        print("Token序列:")
        print("=" * 50)
        print(f"{'类型':<12} {'值':<15} {'位置':<10}")
        print("-" * 50)
        
        for token in self.tokens:
            if token.type == TokenType.EOF:
                break
            location = f"{token.line}:{token.column}"
            print(f"{token.type.name:<12} {token.value:<15} {location}")
        
        non_eof_tokens = [t for t in self.tokens if t.type != TokenType.EOF]
        print("-" * 50)
        print(f"共生成 {len(non_eof_tokens)} 个Token")


def main():
    """测试用例"""
    sql = """
    CREATE TABLE student(
        id INT,
        name VARCHAR(50),
        age INT
    );
    
    INSERT INTO student(id, name, age) VALUES (1, 'Alice', 20);
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
