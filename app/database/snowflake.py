"""Snowflake database connection and query execution."""

import snowflake.connector
from contextlib import contextmanager
from config import settings


class SnowflakeClient:
    """Client for executing queries against Snowflake."""
    
    # Maximum rows to return (safety limit)
    MAX_ROWS = 1000
    
    # Query timeout in seconds
    QUERY_TIMEOUT = 30
    
    def __init__(self):
        self.config = settings.snowflake_config
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = snowflake.connector.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, sql: str) -> list[dict]:
        """
        Execute a SELECT query and return results as a list of dicts.
        
        Args:
            sql: SQL query to execute (must be SELECT)
        
        Returns:
            List of dictionaries, one per row
        
        Raises:
            ValueError: If query is not a SELECT statement
            Exception: Database errors
        """
        sql_stripped = sql.strip().upper()
        if not (sql_stripped.startswith("SELECT") or sql_stripped.startswith("WITH")):
            raise ValueError("Only SELECT queries are allowed")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Set query timeout
                cursor.execute(f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {self.QUERY_TIMEOUT}")
                
                # Execute the query
                cursor.execute(sql)
                
                # Fetch results
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchmany(self.MAX_ROWS)
                
                # Convert to list of dicts
                results = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Convert non-serializable types
                        if hasattr(value, "isoformat"):
                            value = value.isoformat()
                        row_dict[columns[i]] = value
                    results.append(row_dict)
                
                return results
                
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """Test if we can connect to Snowflake."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
        except Exception:
            return False
    
    def get_table_columns(self, table_name: str) -> list[dict]:
        """
        Get column information for a table.
        
        Returns:
            List of {"name": str, "type": str, "nullable": bool}
        """
        sql = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name.upper()}'
        ORDER BY ORDINAL_POSITION
        """
        
        results = self.execute_query(sql)
        return [
            {
                "name": row["COLUMN_NAME"],
                "type": row["DATA_TYPE"],
                "nullable": row["IS_NULLABLE"] == "YES"
            }
            for row in results
        ]
