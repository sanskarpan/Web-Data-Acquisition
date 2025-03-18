# Web Data Acquisition & Crawler Project

A comprehensive web crawling and data extraction system with a user-friendly web interface. This project combines BeautifulSoup, Scrapy, and Selenium to provide robust web scraping capabilities for both static and dynamic websites.

## Features

- **Multi-Engine Crawler**: Uses BeautifulSoup for basic parsing, Scrapy for advanced crawling, and Selenium for JavaScript-heavy websites
- **Flexible Data Extraction**: Define custom CSS selectors to extract specific data from web pages
- **Robust Error Handling**: Comprehensive error handling to ensure reliable crawling
- **Scalable Architecture**: Parallel crawling support with worker threads
- **Multiple Storage Options**: Store data in SQLite, MongoDB, CSV, or JSON formats
- **User-Friendly UI**: Web interface for configuring crawls, monitoring jobs, and visualizing results
- **Data Export**: Export crawled data to CSV or JSON formats
- **Data Visualization**: Charts and statistics to understand your crawled data

## System Requirements

- Python 3.8+
- Chrome browser (for Selenium-based crawling)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/sanskarpan/Web-Data-Acquisition.git
   cd web-crawler
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
web-crawler/
├── app.py                # Flask web application
├── web_crawler.py        # Core crawler implementation
├── database_manager.py   # Database management
├── requirements.txt      # Python dependencies
├── main.py               # Application entry point
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── job_status.html
│   ├── jobs.html
│   ├── data_explorer.html
│   └── visualize.html
├── crawler_data/         # Default location for file-based storage
└── logs/                 # Application logs
```

## Usage

### Starting a New Crawl

1. Enter the URL you want to crawl
2. Set the maximum crawl depth
3. Enable Selenium for JavaScript-heavy sites (optional)
4. Define data extraction selectors
5. Click "Start Crawling"

### Example Selectors

- Title: `title`, `h1`, `.title`
- Content: `p`, `article`, `.content`
- Price: `.price`, `span.price`
- Images: `img`, `.product-image`

### Monitoring Jobs

1. Go to the "Jobs" tab to see all running and completed crawl jobs
2. Click "Details" to view detailed status of a specific job
3. Click "Stop" to cancel a running job

### Exploring Data

1. Go to the "Data" tab to browse crawled data
2. Filter data by URL
3. Export data to CSV or JSON format

### Visualizing Results

Go to the "Visualize" tab to see:
- Domain distribution
- Crawl activity over time
- Overall crawl statistics

## Advanced Usage

### Customizing the Database

By default, the application uses SQLite. To use MongoDB:

```python
db_manager = DatabaseManager(
    db_type="mongodb", 
    connection_params={
        "connection_string": "mongodb://localhost:27017/",
        "db_name": "crawler_data"
    }
)
```

### Using Scrapy for Complex Crawling

For more complex crawling needs, you can use the Scrapy implementation:

```python
from scrapy_crawler import run_scrapy_spider

run_scrapy_spider(
    db_manager=db_manager,
    start_urls=["https://example.com"],
    allowed_domains=["example.com"],
    item_selectors={
        "title": "h1::text",
        "content": "article p::text"
    }
)
```

## API Endpoints

- `/api/job_status/<job_id>`: Get the status of a specific job
- `/api/data`: Get crawled data with optional filters
- `/api/stats`: Get statistics about crawled data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.