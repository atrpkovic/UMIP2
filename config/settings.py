import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        # LLM Providers
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.hyperbolic_api_key = os.getenv("HYPERBOLIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        # Default model
        self.llm_model = os.getenv("LLM_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

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
        missing = []

        # Check for at least one LLM provider
        if not any([self.anthropic_api_key, self.hyperbolic_api_key,
                    self.openai_api_key, self.gemini_api_key]):
            missing.append("At least one LLM API key (ANTHROPIC/HYPERBOLIC/OPENAI/GEMINI)")

        # Check Snowflake configuration
        required = [
            ("SNOWFLAKE_ACCOUNT", self.snowflake_account),
            ("SNOWFLAKE_USER", self.snowflake_user),
            ("SNOWFLAKE_PASSWORD", self.snowflake_password),
            ("SNOWFLAKE_DATABASE", self.snowflake_database),
        ]
        missing.extend([name for name, value in required if not value])

        return missing
