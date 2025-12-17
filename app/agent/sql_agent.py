"""SQL Agent - orchestrates LLM and database interactions."""

import re
from app.agent.llm import LLMClient
from app.agent.prompts import build_system_prompt
from app.database.snowflake import SnowflakeClient
from app.database.schema import get_schema_documentation


class SQLAgent:
    """
    Agent that converts natural language questions to SQL queries
    and returns results with explanations.
    """

    def __init__(self):
        self.llm = LLMClient()
        self.db = SnowflakeClient()
        self.schema_docs = get_schema_documentation()
        self.system_prompt = build_system_prompt(self.schema_docs)

    def set_model(self, model_key: str, model_identifier: str):
        """
        Switch the active LLM model.

        Args:
            model_key: Frontend model key (e.g., 'claude-sonnet', 'deepseek-v3')
            model_identifier: Actual model identifier for the API
        """
        self.llm.set_model(model_key, model_identifier)
    
    def ask(self, question: str) -> dict:
        """
        Process a user question and return an answer.
        
        Args:
            question: Natural language question from the user
        
        Returns:
            {
                "answer": str,      # Natural language response
                "sql": str | None,  # Generated SQL if any
                "data": list | None, # Query results if any
                "error": str | None  # Error message if any
            }
        """
        try:
            # Get LLM response
            llm_response = self.llm.generate(question, self.system_prompt)
            
            # Extract SQL from response if present
            sql_query = self._extract_sql(llm_response)
            
            if not sql_query:
                # No SQL generated - just a conversational response
                return {
                    "answer": llm_response,
                    "sql": None,
                    "data": None,
                    "error": None
                }
            
            # Validate the query is safe
            if not self._is_safe_query(sql_query):
                return {
                    "answer": "I can only run SELECT queries for safety reasons.",
                    "sql": sql_query,
                    "data": None,
                    "error": "Query blocked: only SELECT statements allowed"
                }
            
            # Execute the query
            try:
                results = self.db.execute_query(sql_query)
                
                # Generate a summary of results
                summary = self._summarize_results(question, sql_query, results)
                
                return {
                    "answer": summary,
                    "sql": sql_query,
                    "data": results,
                    "error": None
                }
            except Exception as db_error:
                # Query failed - ask LLM to fix it
                return self._handle_query_error(question, sql_query, str(db_error))
                
        except Exception as e:
            return {
                "answer": "Sorry, I encountered an error processing your question.",
                "sql": None,
                "data": None,
                "error": str(e)
            }
    
    def _extract_sql(self, response: str) -> str | None:
        """Extract SQL query from LLM response."""
        # Look for SQL in code blocks
        sql_pattern = r"```sql\s*(.*?)\s*```"
        matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)

        if matches:
            return matches[0].strip()

        # Fallback: look for SELECT statement outside code blocks
        select_pattern = r"(SELECT\s+.*?(?:;|$))"
        matches = re.findall(select_pattern, response, re.DOTALL | re.IGNORECASE)

        if matches:
            return matches[0].strip().rstrip(";")

        return None

    def _remove_sql_blocks(self, response: str) -> str:
        """Remove SQL code blocks from response text."""
        # Remove ```sql ... ``` blocks
        cleaned = re.sub(r"```sql\s*.*?\s*```", "", response, flags=re.DOTALL | re.IGNORECASE)
        # Remove any other ``` ... ``` blocks that might contain SQL
        cleaned = re.sub(r"```\s*(SELECT\s+.*?)\s*```", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        # Clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        return cleaned.strip()
    
    def _is_safe_query(self, sql: str) -> bool:
        """Check if query is a safe SELECT statement."""
        # Strip SQL comments first
        sql_clean = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)  # Remove single-line comments
        sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)  # Remove multi-line comments
        sql_upper = sql_clean.upper().strip()
        
        # Must start with SELECT or WITH (for CTEs)
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            return False
        
        # Block dangerous keywords
        dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", 
                     "ALTER", "CREATE", "GRANT", "REVOKE", "EXECUTE"]
        
        for keyword in dangerous:
            # Check for keyword as a whole word
            if re.search(rf"\b{keyword}\b", sql_upper):
                return False
        
        return True
    
    def _summarize_results(
        self, 
        question: str, 
        sql: str, 
        results: list[dict]
    ) -> str:
        """Generate a natural language summary of query results."""
        if not results:
            return "The query returned no results."
        
        # For smaller result sets, include all data
        if len(results) <= 20:
            results_to_show = results
            results_note = f"Results ({len(results)} rows):"
        else:
            # For larger sets, show top 20 and summarize
            results_to_show = results[:20]
            results_note = f"Results (showing top 20 of {len(results)} total rows):"
        
        summary_prompt = f"""The user asked: "{question}"

I ran this query:
```sql
{sql}
```

{results_note}
{results_to_show}

Please provide a helpful, conversational answer to the user's question based on these results. 

Guidelines:
- Lead with the key insight or recommendation that directly answers their question
- Highlight the top 3-5 most important items with specific numbers
- Explain WHY these are the best options (e.g., "high search volume + strong April seasonality")
- If relevant, mention any patterns you notice in the data
- Keep it concise but informative — write like you're advising a colleague
- Don't just list data — interpret it and provide actionable recommendations"""
        
        return self.llm.generate(summary_prompt, self.system_prompt)
    
    def _handle_query_error(
        self, 
        question: str, 
        failed_sql: str, 
        error: str
    ) -> dict:
        """Handle a failed query by asking LLM to fix it."""
        fix_prompt = f"""The following query failed:

```sql
{failed_sql}
```

Error: {error}

Original question: "{question}"

Please fix the query and explain what went wrong."""
        
        try:
            response = self.llm.generate(fix_prompt, self.system_prompt)
            fixed_sql = self._extract_sql(response)
            
            if fixed_sql and self._is_safe_query(fixed_sql):
                # Try the fixed query
                results = self.db.execute_query(fixed_sql)
                summary = self._summarize_results(question, fixed_sql, results)
                
                return {
                    "answer": f"(Fixed query) {summary}",
                    "sql": fixed_sql,
                    "data": results,
                    "error": None
                }
        except Exception:
            pass
        
        # Couldn't fix it
        return {
            "answer": f"I generated a query but it failed: {error}",
            "sql": failed_sql,
            "data": None,
            "error": error
        }

    def ask_stream(self, question: str):
        """
        Process a user question and stream the response in real-time.

        Yields events in the format:
            {"type": "token", "content": "text"}
            {"type": "sql", "content": "SELECT ..."}
            {"type": "status", "content": "status message"}
            {"type": "data_ready", "row_count": 123}
            {"type": "complete", "sql": "...", "data": [...]}
            {"type": "error", "content": "error message"}
        """
        try:
            # Phase 1: Collect initial LLM response (SQL generation) WITHOUT streaming
            # We need to process it first to extract and remove SQL blocks
            full_response = ""
            for token in self.llm.generate_stream(question, self.system_prompt):
                full_response += token

            # Extract SQL from the response
            sql_query = self._extract_sql(full_response)

            # Remove SQL code blocks from the displayed response
            display_response = self._remove_sql_blocks(full_response)

            # Now stream the cleaned response to the user
            if display_response:
                for char in display_response:
                    yield {"type": "token", "content": char}

            if not sql_query:
                # No SQL generated - just a conversational response
                yield {
                    "type": "complete",
                    "sql": None,
                    "data": None,
                    "error": None
                }
                return

            # Send the SQL query to frontend
            yield {"type": "sql", "content": sql_query}

            # Validate the query is safe
            if not self._is_safe_query(sql_query):
                yield {
                    "type": "error",
                    "content": "Query blocked: only SELECT statements allowed"
                }
                yield {
                    "type": "complete",
                    "sql": sql_query,
                    "data": None,
                    "error": "Query blocked: only SELECT statements allowed"
                }
                return

            # Execute the query
            yield {"type": "status", "content": "Executing query..."}

            try:
                results = self.db.execute_query(sql_query)

                # Notify that data is ready
                yield {"type": "data_ready", "row_count": len(results)}

                # Phase 2: Stream summary of results
                if not results:
                    yield {"type": "token", "content": "\n\nThe query returned no results."}
                    yield {
                        "type": "complete",
                        "sql": sql_query,
                        "data": [],
                        "error": None
                    }
                    return

                # Generate summary prompt
                if len(results) <= 20:
                    results_to_show = results
                    results_note = f"Results ({len(results)} rows):"
                else:
                    results_to_show = results[:20]
                    results_note = f"Results (showing top 20 of {len(results)} total rows):"

                summary_prompt = f"""The user asked: "{question}"

I ran this query:
```sql
{sql_query}
```

{results_note}
{results_to_show}

Please provide a helpful, conversational answer to the user's question based on these results.

Guidelines:
- Lead with the key insight or recommendation that directly answers their question
- Highlight the top 3-5 most important items with specific numbers
- Explain WHY these are the best options (e.g., "high search volume + strong April seasonality")
- If relevant, mention any patterns you notice in the data
- Keep it concise but informative — write like you're advising a colleague
- Don't just list data — interpret it and provide actionable recommendations"""

                # Add spacing before summary
                yield {"type": "token", "content": "\n\n"}

                # Stream the summary
                for token in self.llm.generate_stream(summary_prompt, self.system_prompt):
                    yield {"type": "token", "content": token}

                # Send completion with full data
                yield {
                    "type": "complete",
                    "sql": sql_query,
                    "data": results,
                    "error": None
                }

            except Exception as db_error:
                # Query execution failed
                yield {"type": "error", "content": f"Query failed: {str(db_error)}"}

                # Try to fix the query
                fix_prompt = f"""The following query failed:

```sql
{sql_query}
```

Error: {db_error}

Original question: "{question}"

Please fix the query and explain what went wrong."""

                yield {"type": "token", "content": "\n\nLet me try to fix that query...\n\n"}

                fixed_response = ""
                for token in self.llm.generate_stream(fix_prompt, self.system_prompt):
                    yield {"type": "token", "content": token}
                    fixed_response += token

                # Try to extract and execute fixed SQL
                fixed_sql = self._extract_sql(fixed_response)

                if fixed_sql and self._is_safe_query(fixed_sql):
                    try:
                        yield {"type": "sql", "content": fixed_sql}
                        yield {"type": "status", "content": "Executing fixed query..."}

                        results = self.db.execute_query(fixed_sql)
                        yield {"type": "data_ready", "row_count": len(results)}

                        yield {
                            "type": "complete",
                            "sql": fixed_sql,
                            "data": results,
                            "error": None
                        }
                        return
                    except Exception:
                        pass

                # Couldn't fix it
                yield {
                    "type": "complete",
                    "sql": sql_query,
                    "data": None,
                    "error": str(db_error)
                }

        except Exception as e:
            yield {"type": "error", "content": f"Error: {str(e)}"}
            yield {
                "type": "complete",
                "sql": None,
                "data": None,
                "error": str(e)
            }