"""Response formatting utilities."""

import json
from typing import Any


def format_results_as_table(results: list[dict], max_rows: int = 20) -> str:
    """
    Format query results as a simple text table.
    
    Args:
        results: List of row dictionaries
        max_rows: Maximum rows to display
    
    Returns:
        Formatted table string
    """
    if not results:
        return "No results"
    
    # Get column names
    columns = list(results[0].keys())
    
    # Calculate column widths
    widths = {col: len(col) for col in columns}
    for row in results[:max_rows]:
        for col in columns:
            val_str = str(row.get(col, ""))[:50]  # Truncate long values
            widths[col] = max(widths[col], len(val_str))
    
    # Build header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)
    
    # Build rows
    lines = [header, separator]
    for row in results[:max_rows]:
        row_str = " | ".join(
            str(row.get(col, ""))[:50].ljust(widths[col]) 
            for col in columns
        )
        lines.append(row_str)
    
    if len(results) > max_rows:
        lines.append(f"... and {len(results) - max_rows} more rows")
    
    return "\n".join(lines)


def truncate_for_display(data: Any, max_length: int = 5000) -> str:
    """
    Truncate data for display in responses.
    
    Args:
        data: Data to format
        max_length: Maximum string length
    
    Returns:
        JSON string, truncated if necessary
    """
    json_str = json.dumps(data, indent=2, default=str)
    
    if len(json_str) <= max_length:
        return json_str
    
    return json_str[:max_length] + "\n... (truncated)"


def format_error_message(error: Exception) -> str:
    """Format an exception into a user-friendly message."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Clean up common Snowflake errors
    if "SQL compilation error" in error_msg:
        # Extract the useful part
        if "does not exist" in error_msg:
            return f"Table or column not found: {error_msg.split('does not exist')[0].split()[-1]}"
    
    return f"{error_type}: {error_msg}"
