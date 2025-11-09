"""
Configuration management for AI4OHS
"""

from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Application configuration"""
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # AI Model Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4")
    
    # Database Configuration
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> bool:
        """Validate configuration"""
        # Basic validation - can be extended
        return True


def get_config() -> Config:
    """Get application configuration"""
    config = Config()
    config.validate()
    return config
