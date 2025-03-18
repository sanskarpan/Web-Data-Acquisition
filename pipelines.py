

import logging
from datetime import datetime

class DatabasePipeline:
    """
    Pipeline to save items to database.
    Requires a database_manager instance to be passed to the spider.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def open_spider(self, spider):
        """Initialize database connection when spider opens."""
        self.db_manager = getattr(spider, 'db_manager', None)
        if not self.db_manager:
            self.logger.warning("No database_manager found in spider. Items won't be saved.")
    
    def process_item(self, item, spider):
        """Process and save item to database."""
        # Convert item to dict
        item_dict = dict(item)
        
        # Add timestamp
        item_dict['crawl_date'] = datetime.now().isoformat()
        
        # Save to database if db_manager is available
        if hasattr(self, 'db_manager') and self.db_manager:
            success = self.db_manager.save_data(item_dict)
            if not success:
                self.logger.error(f"Failed to save item: {item_dict.get('url', 'unknown')}")
        
        return item

