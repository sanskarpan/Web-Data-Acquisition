import logging
import json
import os
import sqlite3
from datetime import datetime
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database manager to handle storing and retrieving crawled data.
    Supports multiple storage backends: SQLite, MongoDB, CSV, JSON.
    """
    
    def __init__(self, db_type="sqlite", connection_params=None):
        """
        Initialize the database manager.
        
        Args:
            db_type: Type of database ('sqlite', 'mongodb', 'csv', 'json')
            connection_params: Connection parameters dictionary
        """
        self.db_type = db_type.lower()
        self.connection_params = connection_params or {}
        self.connection = None
        self.initialized = self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection based on db_type."""
        try:
            if self.db_type == "sqlite":
                db_path = self.connection_params.get("db_path", "crawler_data.db")
                self.connection = sqlite3.connect(db_path)
                self._setup_sqlite_tables()
                return True
            
            elif self.db_type == "mongodb":
                conn_string = self.connection_params.get("connection_string", "mongodb://localhost:27017/")
                db_name = self.connection_params.get("db_name", "crawler_data")
                self.connection = MongoClient(conn_string, serverSelectionTimeoutMS=5000)
                # Check if connection is successful
                self.connection.server_info()
                self.db = self.connection[db_name]
                return True
                
            elif self.db_type in ["csv", "json"]:
                # For file-based storage, no connection needed
                self.data_dir = self.connection_params.get("data_dir", "crawler_data")
                os.makedirs(self.data_dir, exist_ok=True)
                return True
                
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return False
                
        except (sqlite3.Error, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            return False
    
    def _setup_sqlite_tables(self):
        """Set up SQLite tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # Create a table for crawled pages
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawled_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            crawl_date TIMESTAMP,
            data_json TEXT
        )
        ''')
        
        self.connection.commit()
    
    def save_data(self, data):
        """
        Save data to the configured database.
        
        Args:
            data: Dictionary of data to save
        
        Returns:
            bool: Success status
        """
        if not self.initialized:
            logger.error("Database connection not initialized")
            return False
            
        try:
            if self.db_type == "sqlite":
                cursor = self.connection.cursor()
                url = data.get('url')
                # Convert data to JSON string for storage
                data_json = json.dumps(data)
                
                cursor.execute(
                    "INSERT OR REPLACE INTO crawled_pages (url, crawl_date, data_json) VALUES (?, ?, ?)",
                    (url, datetime.now().isoformat(), data_json)
                )
                self.connection.commit()
                return True
                
            elif self.db_type == "mongodb":
                collection = self.db["crawled_pages"]
                # Add timestamp
                data['crawl_date'] = datetime.now()
                # Use URL as unique identifier
                result = collection.update_one(
                    {"url": data['url']},
                    {"$set": data},
                    upsert=True
                )
                return result.acknowledged
                
            elif self.db_type == "csv":
                # Create a DataFrame from data
                df = pd.DataFrame([data])
                # Use URL's domain and path as filename
                url_parts = data.get('url', '').replace('://', '_').replace('/', '_')
                filename = os.path.join(self.data_dir, f"data_{url_parts}.csv")
                
                # Append or create CSV file
                df.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
                return True
                
            elif self.db_type == "json":
                # Create a timestamp
                data['crawl_date'] = datetime.now().isoformat()
                
                # Use URL's domain and path as filename
                url_parts = data.get('url', '').replace('://', '_').replace('/', '_')
                filename = os.path.join(self.data_dir, f"data_{url_parts}.json")
                
                # Read existing data if file exists
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        try:
                            existing_data = json.load(f)
                            if isinstance(existing_data, list):
                                existing_data.append(data)
                            else:
                                existing_data = [existing_data, data]
                        except json.JSONDecodeError:
                            existing_data = [data]
                else:
                    existing_data = [data]
                
                # Write data back to file
                with open(filename, 'w') as f:
                    json.dump(existing_data, f, indent=2)
                    
                return True
                
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return False
    
    def get_data(self, url=None, limit=100):
        """
        Retrieve data from the database.
        
        Args:
            url: Optional URL to filter by
            limit: Maximum number of records to return
            
        Returns:
            list: Retrieved data
        """
        if not self.initialized:
            logger.error("Database connection not initialized")
            return []
            
        try:
            if self.db_type == "sqlite":
                cursor = self.connection.cursor()
                
                if url:
                    cursor.execute(
                        "SELECT data_json FROM crawled_pages WHERE url = ? LIMIT ?",
                        (url, limit)
                    )
                else:
                    cursor.execute(
                        "SELECT data_json FROM crawled_pages LIMIT ?",
                        (limit,)
                    )
                
                results = cursor.fetchall()
                return [json.loads(row[0]) for row in results]
                
            elif self.db_type == "mongodb":
                collection = self.db["crawled_pages"]
                query = {"url": url} if url else {}
                results = collection.find(query).limit(limit)
                return list(results)
                
            elif self.db_type in ["csv", "json"]:
                all_data = []
                
                if url:
                    # Find specific file for URL
                    url_parts = url.replace('://', '_').replace('/', '_')
                    
                    if self.db_type == "csv":
                        filename = os.path.join(self.data_dir, f"data_{url_parts}.csv")
                        if os.path.exists(filename):
                            df = pd.read_csv(filename)
                            all_data = df.to_dict('records')
                            
                    else:  # json
                        filename = os.path.join(self.data_dir, f"data_{url_parts}.json")
                        if os.path.exists(filename):
                            with open(filename, 'r') as f:
                                all_data = json.load(f)
                                
                else:
                    # Get all files
                    for filename in os.listdir(self.data_dir):
                        file_path = os.path.join(self.data_dir, filename)
                        
                        if self.db_type == "csv" and filename.endswith('.csv'):
                            df = pd.read_csv(file_path)
                            all_data.extend(df.to_dict('records'))
                            
                        elif self.db_type == "json" and filename.endswith('.json'):
                            with open(file_path, 'r') as f:
                                file_data = json.load(f)
                                if isinstance(file_data, list):
                                    all_data.extend(file_data)
                                else:
                                    all_data.append(file_data)
                
                # Apply limit
                return all_data[:limit]
                
        except Exception as e:
            logger.error(f"Error retrieving data: {str(e)}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.initialized:
            if self.db_type == "sqlite" and self.connection:
                self.connection.close()
            elif self.db_type == "mongodb" and self.connection:
                self.connection.close()