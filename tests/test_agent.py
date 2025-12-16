"""Tests for the SQL agent."""

import pytest
from app.agent.sql_agent import SQLAgent


class TestSQLExtraction:
    """Test SQL extraction from LLM responses."""
    
    def setup_method(self):
        # Create agent without initializing connections
        self.agent = SQLAgent.__new__(SQLAgent)
    
    def test_extract_sql_from_code_block(self):
        response = """Here's the query:
        
```sql
SELECT * FROM test_table WHERE id = 1
```

This will get you the data."""
        
        result = self.agent._extract_sql(response)
        assert result == "SELECT * FROM test_table WHERE id = 1"
    
    def test_extract_sql_multiline(self):
        response = """```sql
SELECT 
    column1,
    column2
FROM test_table
WHERE status = 'active'
ORDER BY created_at DESC
```"""
        
        result = self.agent._extract_sql(response)
        assert "SELECT" in result
        assert "ORDER BY" in result
    
    def test_no_sql_returns_none(self):
        response = "I don't have enough information to write a query."
        result = self.agent._extract_sql(response)
        assert result is None


class TestQuerySafety:
    """Test query safety validation."""
    
    def setup_method(self):
        self.agent = SQLAgent.__new__(SQLAgent)
    
    def test_select_is_safe(self):
        assert self.agent._is_safe_query("SELECT * FROM table")
    
    def test_with_cte_is_safe(self):
        query = "WITH cte AS (SELECT 1) SELECT * FROM cte"
        assert self.agent._is_safe_query(query)
    
    def test_insert_blocked(self):
        assert not self.agent._is_safe_query("INSERT INTO table VALUES (1)")
    
    def test_update_blocked(self):
        assert not self.agent._is_safe_query("UPDATE table SET col = 1")
    
    def test_delete_blocked(self):
        assert not self.agent._is_safe_query("DELETE FROM table")
    
    def test_drop_blocked(self):
        assert not self.agent._is_safe_query("DROP TABLE users")
    
    def test_case_insensitive(self):
        assert not self.agent._is_safe_query("insert INTO table VALUES (1)")
        assert not self.agent._is_safe_query("DROP table users")


class TestSchemaDocumentation:
    """Test schema documentation generation."""
    
    def test_schema_docs_not_empty(self):
        from app.database.schema import get_schema_documentation
        docs = get_schema_documentation()
        assert len(docs) > 0
        assert "PRIORITY_TIRE_DB" in docs
    
    def test_all_tables_included(self):
        from app.database.schema import get_schema_documentation, get_table_names
        docs = get_schema_documentation()
        
        for table_name in get_table_names():
            assert table_name in docs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
