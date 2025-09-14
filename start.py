#!/usr/bin/env python3
"""
Application startup script
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.init_db import init_database, check_database_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "GCP_PROJECT_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file or environment configuration")
        return False
    
    return True


def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        import uvicorn
        logger.info("Core dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return False


def setup_database():
    """Initialize database if needed"""
    try:
        # Check database health
        if not check_database_health():
            logger.info("Database not initialized, creating tables...")
            init_database()
        else:
            logger.info("Database is healthy")
        return True
    except Exception as e:
        logger.error(f"Failed to setup database: {e}")
        return False


def start_development_server():
    """Start development server with auto-reload"""
    try:
        logger.info("Starting development server...")
        logger.info(f"Server will be available at: http://localhost:8000")
        logger.info(f"API documentation: http://localhost:8000/docs")
        logger.info("Press Ctrl+C to stop the server")
        
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        sys.exit(1)


def start_production_server():
    """Start production server"""
    try:
        logger.info("Starting production server...")
        logger.info(f"Server will be available at: http://0.0.0.0:8000")
        
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "4",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start production server: {e}")
        sys.exit(1)


def run_tests():
    """Run test suite"""
    try:
        logger.info("Running test suite...")
        subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--cov=app",
            "--cov-report=html"
        ])
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        sys.exit(1)


def run_linting():
    """Run code linting and formatting"""
    try:
        logger.info("Running code linting...")
        
        # Run black formatter
        subprocess.run([sys.executable, "-m", "black", "app/", "tests/"])
        
        # Run isort
        subprocess.run([sys.executable, "-m", "isort", "app/", "tests/"])
        
        # Run flake8
        subprocess.run([sys.executable, "-m", "flake8", "app/", "tests/"])
        
        logger.info("Code linting completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to run linting: {e}")
        sys.exit(1)


def show_help():
    """Show help message"""
    print("""
FinCompliance RAG Portal - Startup Script

Usage:
    python start.py [command] [options]

Commands:
    dev         Start development server with auto-reload
    prod        Start production server
    test        Run test suite
    lint        Run code linting and formatting
    init-db     Initialize database
    health      Check database health
    help        Show this help message

Examples:
    python start.py dev              # Start development server
    python start.py prod             # Start production server
    python start.py test             # Run tests
    python start.py lint             # Run linting
    python start.py init-db          # Initialize database
    python start.py health           # Check database health

Environment Variables:
    SECRET_KEY              - Secret key for JWT tokens
    DATABASE_URL            - Database connection URL
    GCP_PROJECT_ID          - Google Cloud Project ID
    OPENAI_API_KEY          - OpenAI API key (optional)
    VERTEX_AI_LOCATION      - Vertex AI location (optional)

For more information, see README.md
""")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Check environment and dependencies
    if command not in ["help", "health"]:
        if not check_environment():
            sys.exit(1)
        
        if not check_dependencies():
            sys.exit(1)
    
    # Execute command
    if command == "dev":
        if not setup_database():
            sys.exit(1)
        start_development_server()
    elif command == "prod":
        if not setup_database():
            sys.exit(1)
        start_production_server()
    elif command == "test":
        run_tests()
    elif command == "lint":
        run_linting()
    elif command == "init-db":
        init_database()
    elif command == "health":
        check_database_health()
    elif command == "help":
        show_help()
    else:
        logger.error(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
