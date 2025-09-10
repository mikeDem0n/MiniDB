"""
抽象语法树节点定义
用于表示解析后的SQL语句结构
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict


class ASTNode(ABC):
    """AST节点基类"""
    
    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
    
    @abstractmethod
    def accept(self, visitor):
        """访问者模式接口"""
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}()"


class Statement(ASTNode):
    """SQL语句基类"""
    pass


class Expression(ASTNode):
    """表达式基类"""
    pass


class DataType(ASTNode):
    """数据类型节点"""
    
    def __init__(self, type_name: str, size: Optional[int] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.type_name = type_name.upper()
        self.size = size
    
    def accept(self, visitor):
        return visitor.visit_data_type(self)
    
    def __repr__(self):
        if self.size:
            return f"DataType({self.type_name}({self.size}))"
        return f"DataType({self.type_name})"


class Identifier(Expression):
    """标识符节点"""
    
    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name
    
    def accept(self, visitor):
        return visitor.visit_identifier(self)
    
    def __repr__(self):
        return f"Identifier({self.name})"


class Literal(Expression):
    """字面量节点"""
    
    def __init__(self, value: Any, data_type: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value
        self.data_type = data_type
    
    def accept(self, visitor):
        return visitor.visit_literal(self)
    
    def __repr__(self):
        return f"Literal({self.value}, {self.data_type})"


class ColumnDef(ASTNode):
    """列定义节点"""
    
    def __init__(self, name: str, data_type: DataType, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name
        self.data_type = data_type
    
    def accept(self, visitor):
        return visitor.visit_column_def(self)
    
    def __repr__(self):
        return f"ColumnDef({self.name}, {self.data_type})"


class BinaryExpression(Expression):
    """二元表达式节点"""
    
    def __init__(self, left: Expression, operator: str, right: Expression, 
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_binary_expression(self)
    
    def __repr__(self):
        return f"BinaryExpression({self.left} {self.operator} {self.right})"


class CreateTableStatement(Statement):
    """CREATE TABLE语句节点"""
    
    def __init__(self, table_name: str, columns: List[ColumnDef], 
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.table_name = table_name
        self.columns = columns
    
    def accept(self, visitor):
        return visitor.visit_create_table_statement(self)
    
    def __repr__(self):
        return f"CreateTableStatement({self.table_name}, {self.columns})"


class InsertStatement(Statement):
    """INSERT语句节点"""
    
    def __init__(self, table_name: str, columns: Optional[List[str]], 
                 values: List[List[Expression]], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.table_name = table_name
        self.columns = columns
        self.values = values
    
    def accept(self, visitor):
        return visitor.visit_insert_statement(self)
    
    def __repr__(self):
        return f"InsertStatement({self.table_name}, {self.columns}, {self.values})"


class SelectStatement(Statement):
    """SELECT语句节点"""
    
    def __init__(self, select_list: List[Expression], from_table: str, 
                 where_clause: Optional[Expression] = None, 
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.select_list = select_list
        self.from_table = from_table
        self.where_clause = where_clause
    
    def accept(self, visitor):
        return visitor.visit_select_statement(self)
    
    def __repr__(self):
        return f"SelectStatement({self.select_list}, {self.from_table}, {self.where_clause})"


class DeleteStatement(Statement):
    """DELETE语句节点"""
    
    def __init__(self, table_name: str, where_clause: Optional[Expression] = None,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.table_name = table_name
        self.where_clause = where_clause
    
    def accept(self, visitor):
        return visitor.visit_delete_statement(self)
    
    def __repr__(self):
        return f"DeleteStatement({self.table_name}, {self.where_clause})"


class SQLProgram(ASTNode):
    """SQL程序节点，包含多个语句"""
    
    def __init__(self, statements: List[Statement], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.statements = statements
    
    def accept(self, visitor):
        return visitor.visit_sql_program(self)
    
    def __repr__(self):
        return f"SQLProgram({self.statements})"


# 访问者接口
class ASTVisitor(ABC):
    """AST访问者接口"""
    
    @abstractmethod
    def visit_data_type(self, node: DataType):
        pass
    
    @abstractmethod
    def visit_identifier(self, node: Identifier):
        pass
    
    @abstractmethod
    def visit_literal(self, node: Literal):
        pass
    
    @abstractmethod
    def visit_column_def(self, node: ColumnDef):
        pass
    
    @abstractmethod
    def visit_binary_expression(self, node: BinaryExpression):
        pass
    
    @abstractmethod
    def visit_create_table_statement(self, node: CreateTableStatement):
        pass
    
    @abstractmethod
    def visit_insert_statement(self, node: InsertStatement):
        pass
    
    @abstractmethod
    def visit_select_statement(self, node: SelectStatement):
        pass
    
    @abstractmethod
    def visit_delete_statement(self, node: DeleteStatement):
        pass
    
    @abstractmethod
    def visit_sql_program(self, node: SQLProgram):
        pass
