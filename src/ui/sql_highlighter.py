from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression
from ..core.theme_manager import theme_manager


# SQL 关键字定义 - 按数据库类型分类
SQL_KEYWORDS = {
    # 通用关键字（所有数据库）
    'common': [
        # DDL
        'CREATE', 'TABLE', 'ALTER', 'DROP', 'INDEX', 'VIEW', 'TRIGGER',
        'PROCEDURE', 'FUNCTION', 'DATABASE', 'SCHEMA', 'COLUMN',
        # DML
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'INTO', 'VALUES',
        'SET', 'WHERE', 'FROM', 'JOIN', 'LEFT', 'RIGHT', 'INNER',
        'OUTER', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE',
        # 约束
        'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT',
        'UNIQUE', 'CHECK', 'DEFAULT', 'NULL',
        # 其他
        'AS', 'IF', 'EXISTS', 'REPLACE', 'USING', 'WITH',
        'ADD', 'MODIFY', 'CHANGE', 'RENAME', 'COMMENT',
        'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
        'DISTINCT', 'ALL', 'ASC', 'DESC',
        'UNION', 'EXCEPT', 'INTERSECT',
        'BEGIN', 'END', 'DECLARE', 'RETURN', 'RETURNS',
        'CASE', 'WHEN', 'THEN', 'ELSE',
        'ON', 'DO', 'NOTHING',
    ],
    
    # MySQL 特有关键字
    'mysql': [
        'AUTO_INCREMENT', 'ENGINE', 'CHARSET', 'COLLATE',
        'TINYINT', 'SMALLINT', 'MEDIUMINT', 'INT', 'INTEGER', 'BIGINT',
        'DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL',
        'DATE', 'DATETIME', 'TIMESTAMP', 'TIME', 'YEAR',
        'CHAR', 'VARCHAR', 'TINYTEXT', 'MEDIUMTEXT', 'LONGTEXT',
        'TINYBLOB', 'BLOB', 'MEDIUMBLOB', 'LONGBLOB',
        'ENUM', 'SET', 'BOOLEAN', 'BOOL',
        'UNSIGNED', 'ZEROFILL', 'SIGNED',
        'BINARY', 'VARBINARY',
        'REGEXP', 'RLIKE', 'SOUNDS', 'XOR',
        'SHOW', 'DESCRIBE', 'EXPLAIN', 'USE',
        'TRUNCATE', 'FLUSH', 'RESET',
        'TEMPORARY', 'TEMP',
        'IFNULL', 'ISNULL',
        'FIRST', 'AFTER', 'BEFORE',
        'STRAIGHT_JOIN',
        'LOCK', 'UNLOCK', 'TABLES',
    ],
    
    # PostgreSQL 特有关键字
    'postgresql': [
        'SERIAL', 'BIGSERIAL', 'SMALLSERIAL',
        'PLPGSQL', 'LANGUAGE', 'IMMUTABLE', 'STABLE', 'VOLATILE',
        'SETOF', 'ARRAY', 'JSON', 'JSONB',
        'UUID', 'INET', 'CIDR', 'MACADDR',
        'ILIKE', 'SIMILAR', 'TO',
        'WINDOW', 'PARTITION', 'OVER', 'RANGE',
        'ROWS', 'GROUPS', 'UNBOUNDED', 'PRECEDING', 'FOLLOWING',
        'CURRENT_ROW', 'EXCLUDE', 'TIES', 'OTHERS',
        'DEFERRABLE', 'INITIALLY', 'DEFERRED', 'IMMEDIATE',
        'EXTENSION', 'TABLESPACE', 'SEQUENCE',
        'OWNED', 'DEPENDS', 'COLLATION', 'OPERATOR',
        'AGGREGATE', 'DOMAIN', 'TYPE', 'ACCESS', 'METHOD',
        'ROLE', 'MEMBER', 'ADMIN', 'CREATEDB', 'CREATEROLE',
        'SUPERUSER', 'REPLICATION', 'BYPASSRLS',
        'CONNECTION', 'CONFLICT',
        'MATERIALIZED', 'REFRESH', 'CONCURRENTLY',
        'ANALYZE', 'VERBOSE', 'COSTS', 'BUFFERS', 'TIMING',
        'TEXT', 'BOOLEAN', 'BOOL',
        'SMALLINT', 'INT', 'INTEGER', 'BIGINT',
        'DECIMAL', 'NUMERIC', 'REAL', 'DOUBLE', 'PRECISION',
        'CHARACTER', 'CHAR', 'VARCHAR', 'TEXT',
        'TIMESTAMP', 'INTERVAL',
    ],
    
    # SQL Server 特有关键字
    'sqlserver': [
        'NVARCHAR', 'NCHAR', 'NTEXT',
        'IDENTITY', 'ROWVERSION', 'TIMESTAMP',
        'OUTPUT', 'MERGE', 'TOP', 'PERCENT', 'TIES',
        'PIVOT', 'UNPIVOT', 'APPLY',
        'CTE', 'OPTION', 'RECOMPILE',
        'SCHEMABINDING', 'ENCRYPTION',
        'READONLY', 'UPDATABLE', 'INSTEAD', 'OF',
        'AFTER', 'FOR', 'ATTACH', 'REBUILD',
        'DBCC', 'NOCOUNT', 'ANSI_NULLS',
        'QUOTED_IDENTIFIER', 'PAD_INDEX', 'FILLFACTOR',
        'IGNORE_DUP_KEY', 'STATISTICS_NORECOMPUTE',
        'ALLOW_ROW_LOCKS', 'ALLOW_PAGE_LOCKS',
        'ONLINE', 'MAXDOP', 'DATA_COMPRESSION',
        'CLUSTERED', 'NONCLUSTERED', 'INCLUDE',
        'GO', 'EXEC', 'SP_EXECUTESQL',
        'BIT', 'UNIQUEIDENTIFIER', 'SMALLDATETIME', 'DATETIME2', 'DATETIMEOFFSET',
        'SQL_VARIANT', 'TABLE', 'HIERARCHYID', 'GEOMETRY', 'GEOGRAPHY',
    ],
}


class SQLHighlighter(QSyntaxHighlighter):
    """SQL 语法高亮器"""
    
    def __init__(self, parent=None, db_type=None):
        super().__init__(parent)
        self.db_type = db_type  # 数据库类型：mysql, postgresql, sqlserver 等
        self._update_colors()
        # 监听主题变化
        theme_manager.register_callback(self._on_theme_changed)
    
    def _get_keywords(self):
        """根据数据库类型获取关键字列表"""
        keywords = set(SQL_KEYWORDS['common'])
        
        # 添加特定数据库的关键字
        if self.db_type and self.db_type in SQL_KEYWORDS:
            keywords.update(SQL_KEYWORDS[self.db_type])
        
        return sorted(keywords)
    
    def _on_theme_changed(self, theme):
        """主题变化时更新颜色并重新高亮"""
        self._update_colors()
        # 重新应用高亮
        self.rehighlight()
    
    def _update_colors(self):
        """根据主题更新颜色"""
        if theme_manager.is_dark:
            # 黑夜主题颜色
            self.keyword_color = QColor("#569CD6")      # 蓝色 - 关键字
            self.string_color = QColor("#CE9178")        # 橙色 - 字符串
            self.comment_color = QColor("#6A9955")       # 绿色 - 注释
            self.number_color = QColor("#B5CEA8")        # 浅绿 - 数字
            self.identifier_color = QColor("#9CDCFE")    # 浅蓝 - 标识符
            self.operator_color = QColor("#D4D4D4")      # 白色 - 操作符
            self.function_color = QColor("#DCDCAA")      # 黄色 - 函数
        else:
            # 白天主题颜色
            self.keyword_color = QColor("#0000FF")       # 蓝色 - 关键字
            self.string_color = QColor("#A31515")        # 红色 - 字符串
            self.comment_color = QColor("#008000")       # 绿色 - 注释
            self.number_color = QColor("#098658")        # 深绿 - 数字
            self.identifier_color = QColor("#001080")    # 深蓝 - 标识符
            self.operator_color = QColor("#000000")      # 黑色 - 操作符
            self.function_color = QColor("#795E26")      # 棕色 - 函数
    
    def highlightBlock(self, text):
        """高亮文本块"""
        self._highlight_keywords(text)
        self._highlight_strings(text)
        self._highlight_comments(text)
        self._highlight_numbers(text)
        self._highlight_functions(text)
    
    def _highlight_keywords(self, text):
        """高亮 SQL 关键字"""
        keywords = self._get_keywords()
        
        # 组合关键字正则
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        regex = QRegularExpression(keyword_pattern, QRegularExpression.CaseInsensitiveOption)
        
        match_iterator = regex.globalMatch(text)
        while match_iterator.hasNext():
            match = match_iterator.next()
            word = match.captured(0)
            
            # 跳过字符串内的关键字（简单判断：前面有奇数个引号）
            pos = match.capturedStart()
            if pos > 0 and text[:pos].count("'") % 2 == 1:
                continue
            
            fmt = QTextCharFormat()
            fmt.setForeground(self.keyword_color)
            fmt.setFontWeight(QFont.Bold)
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
    
    def _highlight_strings(self, text):
        """高亮字符串（单引号）"""
        # 匹配单引号字符串，包括转义
        regex = QRegularExpression(r"'(?:[^'\\]|\\.)*'")
        match_iterator = regex.globalMatch(text)
        while match_iterator.hasNext():
            match = match_iterator.next()
            fmt = QTextCharFormat()
            fmt.setForeground(self.string_color)
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
    
    def _highlight_comments(self, text):
        """高亮注释"""
        # 单行注释 --
        regex1 = QRegularExpression(r'--.*$')
        match_iterator = regex1.globalMatch(text)
        while match_iterator.hasNext():
            match = match_iterator.next()
            fmt = QTextCharFormat()
            fmt.setForeground(self.comment_color)
            fmt.setFontItalic(True)
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
        
        # 多行注释 /* */ (简化版，只处理单行内的)
        regex2 = QRegularExpression(r'/\*.*?\*/')
        match_iterator = regex2.globalMatch(text)
        while match_iterator.hasNext():
            match = match_iterator.next()
            fmt = QTextCharFormat()
            fmt.setForeground(self.comment_color)
            fmt.setFontItalic(True)
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
    
    def _highlight_numbers(self, text):
        """高亮数字"""
        regex = QRegularExpression(r'\b\d+(?:\.\d+)?\b')
        match_iterator = regex.globalMatch(text)
        while match_iterator.hasNext():
            match = match_iterator.next()
            # 跳过字符串内的数字
            pos = match.capturedStart()
            if pos > 0 and text[:pos].count("'") % 2 == 1:
                continue
            
            fmt = QTextCharFormat()
            fmt.setForeground(self.number_color)
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
    
    def _highlight_functions(self, text):
        """高亮函数调用"""
        functions = [
            'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CONCAT', 'SUBSTRING',
            'LENGTH', 'UPPER', 'LOWER', 'TRIM', 'NOW', 'CURDATE', 'CURTIME',
            'DATE', 'TIME', 'YEAR', 'MONTH', 'DAY', 'IFNULL', 'COALESCE',
            'CAST', 'CONVERT', 'ABS', 'ROUND', 'CEIL', 'FLOOR',
            'CURRENT_TIMESTAMP', 'CURRENT_DATE', 'CURRENT_TIME',
        ]
        
        # 函数名后跟左括号
        func_pattern = r'\b(' + '|'.join(functions) + r')\s*\('
        regex = QRegularExpression(func_pattern, QRegularExpression.CaseInsensitiveOption)
        
        match_iterator = regex.globalMatch(text)
        while match_iterator.hasNext():
            match = match_iterator.next()
            # 只高亮函数名部分（不包括左括号）
            func_name = match.captured(1)
            fmt = QTextCharFormat()
            fmt.setForeground(self.function_color)
            self.setFormat(match.capturedStart(), len(func_name), fmt)
