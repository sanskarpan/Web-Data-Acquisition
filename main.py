# main.py
import os
import logging
from flask import Flask

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import our custom modules
from web_crawler import WebCrawler
from database_manager import DatabaseManager
from app import app

def setup_project():
    """Set up the project structure and ensure all dependencies are available."""
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('crawler_data', exist_ok=True)
    
    # Check for required dependencies
    try:
        import bs4
        import requests
        import selenium
        import flask
        import pandas
        logger.info("All required dependencies are available")
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        logger.info("Please run: pip install -r requirements.txt")
        return False

    return True

def create_requirements_file():
    """Create requirements.txt file with all dependencies."""
    requirements = [
        "beautifulsoup4==4.12.2",
        "requests==2.31.0",
        "selenium==4.16.0",
        "webdriver-manager==4.0.1",
        "scrapy==2.11.0",
        "flask==3.0.0",
        "pandas==2.1.3",
        "pymongo==4.6.1"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    logger.info("Created requirements.txt file")

def test_crawler():
    """Test the crawler functionality with a sample URL."""
    db_manager = DatabaseManager(db_type="sqlite", connection_params={"db_path": "test.db"})
    crawler = WebCrawler(database_manager=db_manager)
    
    test_url = "https://example.com"
    test_selectors = {
        "title": "h1",
        "description": "p"
    }
    
    logger.info(f"Testing crawler with URL: {test_url}")
    try:
        data = crawler.extract_data(test_url, test_selectors)
        logger.info(f"Crawler test successful. Extracted data: {data}")
        crawler.close()
        return True
    except Exception as e:
        logger.error(f"Crawler test failed: {str(e)}")
        crawler.close()
        return False

def main():
    """Main entry point of the application."""
    logger.info("Starting Web Crawler Application")
    
    # Set up the project
    if not setup_project():
        logger.error("Project setup failed")
        return
    
    # Create requirements file
    create_requirements_file()
    
    # Test crawler functionality
    test_crawler()
    
    # Start the Flask application
    logger.info("Starting Flask web server")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()