import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        # Anthropic
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Snowflake
        self.snowflake_account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.snowflake_user = os.getenv("SNOWFLAKE_USER")
        self.snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")
        self.snowflake_warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        self.snowflake_database = os.getenv("SNOWFLAKE_DATABASE")
        self.snowflake_schema = os.getenv("SNOWFLAKE_SCHEMA")
        
        # Flask
        self.flask_secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key-change-in-prod")
        self.flask_debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    @property
    def snowflake_config(self) -> dict:
        """Return Snowflake connection parameters as a dict."""
        return {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "password": self.snowflake_password,
            "warehouse": self.snowflake_warehouse,
            "database": self.snowflake_database,
            "schema": self.snowflake_schema,
        }
    
    def validate(self) -> list[str]:
        """Check for missing required configuration. Returns list of missing vars."""
        required = [
            ("ANTHROPIC_API_KEY", self.anthropic_api_key),
            ("SNOWFLAKE_ACCOUNT", self.snowflake_account),
            ("SNOWFLAKE_USER", self.snowflake_user),
            ("SNOWFLAKE_PASSWORD", self.snowflake_password),
            ("SNOWFLAKE_DATABASE", self.snowflake_database),
        ]
        return [name for name, value in required if not value]
