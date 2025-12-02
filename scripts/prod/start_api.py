"""
API Server Launcher for Production
Runs FastAPI with Uvicorn in production mode with comprehensive error handling
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Configure logging before imports
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("logs/dev/api_startup.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def validate_environment() -> tuple[bool, Optional[str]]:
    """
    Validate environment configuration before starting server.

    Returns:
        (is_valid, error_message)
    """
    try:
        # Check .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            return False, "Missing .env file (required for configuration)"

        # Validate required directories exist
        required_dirs = [
            Path("logs/dev"),
            Path("logs/pipelines"),
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                logger.warning(f"Creating missing directory: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)

        # Validate Python version (3.10+)
        if sys.version_info < (3, 10):
            return (
                False,
                f"Python 3.10+ required (current: {sys.version_info.major}.{sys.version_info.minor})",
            )

        # Check port availability
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("0.0.0.0", 8000))
            sock.close()
        except OSError:
            return False, "Port 8000 already in use"

        return True, None

    except Exception as e:
        return False, f"Environment validation failed: {e}"


def main():
    """Main entry point with error handling."""
    try:
        # Add project root to path
        project_root = Path(__file__).parents[2].resolve()
        sys.path.insert(0, str(project_root))

        logger.info(f"Starting API server from: {project_root}")

        # Validate environment
        is_valid, error_msg = validate_environment()
        if not is_valid:
            logger.error(f"Environment validation failed: {error_msg}")
            sys.exit(1)

        logger.info("✓ Environment validation passed")

        # Import after path setup
        try:
            import uvicorn

            from src.ohs.api.main import app
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            logger.error("Ensure all dependencies are installed: pip install -r requirements.txt")
            sys.exit(1)

        # Start server with error handling
        logger.info("Starting Uvicorn server on 0.0.0.0:8000")

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            workers=4,
            timeout_keep_alive=60,
            limit_concurrency=1000,
            limit_max_requests=10000,
        )

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error starting API server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
