"""
模式目录管理器
负责维护数据库的元数据信息，包括表结构、列信息等
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class ColumnInfo:
    """列信息"""

    name: str
    data_type: str
    size: Optional[int] = None
    is_nullable: bool = True

    def __repr__(self):
        if self.size:
            return f"{self.name} {self.data_type}({self.size})"
        return f"{self.name} {self.data_type}"


@dataclass
class TableInfo:
    """表信息"""

    name: str
    columns: List[ColumnInfo]

    def get_column(self, column_name: str) -> Optional[ColumnInfo]:
        """根据列名获取列信息"""
        for col in self.columns:
            if col.name.upper() == column_name.upper():
                return col
        return None

    def get_column_names(self) -> List[str]:
        """获取所有列名"""
        return [col.name for col in self.columns]

    def __repr__(self):
        return f"TableInfo({self.name}, {self.columns})"


class Catalog:
    """模式目录管理器"""

    def __init__(self):
        self._tables: Dict[str, TableInfo] = {}

    def create_table(self, table_name: str, columns: List[ColumnInfo]) -> bool:
        """创建表"""
        table_key = table_name.upper()

        if table_key in self._tables:
            return False  # 表已存在

        self._tables[table_key] = TableInfo(table_name, columns)
        return True

    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        table_key = table_name.upper()

        if table_key not in self._tables:
            return False  # 表不存在

        del self._tables[table_key]
        return True

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        return table_name.upper() in self._tables

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """检查列是否存在"""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return False
        return table_info.get_column(column_name) is not None

    def get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """获取表信息"""
        return self._tables.get(table_name.upper())

    def get_column_info(
        self, table_name: str, column_name: str
    ) -> Optional[ColumnInfo]:
        """获取列信息"""
        table_info = self.get_table_info(table_name)
        if table_info:
            return table_info.get_column(column_name)
        return None

    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        return [table.name for table in self._tables.values()]

    def validate_columns(
        self, table_name: str, column_names: List[str]
    ) -> Tuple[bool, str]:
        """验证列是否存在"""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return False, f"Table '{table_name}' does not exist"

        table_columns = [col.name.upper() for col in table_info.columns]

        for col_name in column_names:
            if col_name.upper() not in table_columns:
                return (
                    False,
                    f"Column '{col_name}' does not exist in table '{table_name}'",
                )

        return True, ""

    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """获取列的数据类型"""
        col_info = self.get_column_info(table_name, column_name)
        return col_info.data_type if col_info else None

    def clear(self):
        """清空目录"""
        self._tables.clear()

    def to_dict(self) -> Dict:
        """转换为字典格式，用于序列化"""
        result = {}
        for table_name, table_info in self._tables.items():
            result[table_name] = {
                "name": table_info.name,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "size": col.size,
                        "is_nullable": col.is_nullable,
                    }
                    for col in table_info.columns
                ],
            }
        return result

    def from_dict(self, data: Dict):
        """从字典格式恢复，用于反序列化"""
        self._tables.clear()

        for table_name, table_data in data.items():
            columns = []
            for col_data in table_data["columns"]:
                column = ColumnInfo(
                    name=col_data["name"],
                    data_type=col_data["data_type"],
                    size=col_data.get("size"),
                    is_nullable=col_data.get("is_nullable", True),
                )
                columns.append(column)

            self._tables[table_name] = TableInfo(table_data["name"], columns)

    def __repr__(self):
        return f"Catalog({list(self._tables.keys())})"
