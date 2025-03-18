# config.py
import os
import json
import logging
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Default configuration
DEFAULT_CONFIG = {
    # General settings
    "app_name": "Web Crawler Dashboard",
    "debug": False,
    "log_level": "INFO",
    "log_file": "crawler_app.log",
    
    # Server settings
    "host": "0.0.0.0",
    "port": 5000,
    
    # Crawler settings
    "default_max_depth": 3,
    "concurrent_requests": 5,
    "request_timeout": 10,
    "respect_robots_txt": True,
    "user_agent": "WebCrawler/1.0 (+https://example.com/bot)",
    "follow_redirects": True,
    "retry_failed_requests": True,
    "max_retries": 3,
    "retry_delay": 2,
    
    # Selenium settings
    "selenium_enabled": True,
    "headless": True,
    "selenium_timeout": 10,
    "wait_for_js": 2,
    
    # Database settings
    "db_type": "sqlite",
    "sqlite_path": "crawler_data.db",
    "mongodb_connection": "mongodb://localhost:27017/",
    "mongodb_db_name": "crawler_data",
    
    # Storage settings
    "data_dir": "crawler_data",
    "screenshots_dir": "screenshots",
    "downloads_dir": "downloads",
    
    # Rate limiting
    "rate_limit_enabled": True,
    "rate_limit_requests": 10,
    "rate_limit_period": 1,  # in seconds
    
    # Export settings
    "max_export_items": 10000,
    
    # UI settings
    "items_per_page": 20,
    "enable_dark_mode": False,
    "date_format": "%Y-%m-%d %H:%M:%S"
}

class Config:
    """Configuration manager for the crawler application."""
    
    def __init__(self, config_file="config.json"):
        """
        Initialize with default config and load from file if it exists.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = os.path.join(BASE_DIR, config_file)
        self.config = DEFAULT_CONFIG.copy()
        
        # Load configuration from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    logging.info(f"Loaded configuration from {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error loading config from {self.config_file}: {str(e)}")
                logging.info("Using default configuration")
        else:
            logging.info(f"Config file {self.config_file} not found. Using default configuration.")
            # Create default config file
            self.save_config()
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            bool: Success status
        """
        self.config[key] = value
        return self.save_config()
    
    def save_config(self):
        """
        Save configuration to file.
        
        Returns:
            bool: Success status
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info(f"Configuration saved to {self.config_file}")
            return True
        except IOError as e:
            logging.error(f"Error saving configuration to {self.config_file}: {str(e)}")
            return False
    
    def get_database_config(self):
        """
        Get database configuration.
        
        Returns:
            tuple: (db_type, connection_params)
        """
        db_type = self.get("db_type", "sqlite")
        
        if db_type == "sqlite":
            connection_params = {
                "db_path": self.get("sqlite_path", "crawler_data.db")
            }
        elif db_type == "mongodb":
            connection_params = {
                "connection_string": self.get("mongodb_connection", "mongodb://localhost:27017/"),
                "db_name": self.get("mongodb_db_name", "crawler_data")
            }
        else:
            # File-based storage
            connection_params = {
                "data_dir": self.get("data_dir", "crawler_data")
            }
        
        return db_type, connection_params
    
    def get_crawler_config(self):
        """
        Get crawler configuration.
        
        Returns:
            dict: Crawler configuration
        """
        return {
            "max_depth": self.get("default_max_depth", 3),
            "concurrent_requests": self.get("concurrent_requests", 5),
            "timeout": self.get("request_timeout", 10),
            "respect_robots_txt": self.get("respect_robots_txt", True),
            "user_agent": self.get("user_agent", "WebCrawler/1.0"),
            "follow_redirects": self.get("follow_redirects", True),
            "retry_failed_requests": self.get("retry_failed_requests", True),
            "max_retries": self.get("max_retries", 3),
            "retry_delay": self.get("retry_delay", 2),
            "selenium_enabled": self.get("selenium_enabled", True),
            "headless": self.get("headless", True),
            "selenium_timeout": self.get("selenium_timeout", 10),
            "wait_for_js": self.get("wait_for_js", 2)
        }
    
    def to_dict(self):
        """
        Get entire configuration as dictionary.
        
        Returns:
            dict: Configuration dictionary
        """
        return self.config.copy()

# Create a singleton instance
config = Config()