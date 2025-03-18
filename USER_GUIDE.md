# Web Crawler User Guide

This guide will help you get started with the Web Crawler application, explaining how to install it, use the web interface, and run the command-line tools.

## Table of Contents

1. [Installation](#installation)
2. [Web Interface](#web-interface)
3. [Command-Line Interface](#command-line-interface)
4. [Advanced Configuration](#advanced-configuration)
5. [Troubleshooting](#troubleshooting)

## Installation

### Standard Installation

1. Clone the repository:
   ```
   git clone https://github.com/sanskarpan/Web-Data-Acquisition.git
   cd web-crawler
   ```

2. Run the installation script:
   ```
   chmod +x install.sh
   ./install.sh
   ```

3. Start the web server:
   ```
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   python main.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

### Docker Installation

If you prefer using Docker:

1. Make sure Docker and Docker Compose are installed on your system
2. Clone the repository
3. Run Docker Compose:
   ```
   docker-compose up -d
   ```
4. Access the application at `http://localhost:5000`

## Web Interface

The web interface provides an intuitive way to configure and monitor crawling jobs, explore extracted data, and visualize results.

### Starting a New Crawl

1. On the home page, fill in the crawl configuration form:
   - **Start URL**: The URL where crawling will begin
   - **Max Depth**: How many levels of links to follow (1-10)
   - **Use Selenium**: Check this for JavaScript-heavy sites
   - **Restrict to Same Domain**: Check to avoid crawling external links
   - **Data Extraction Selectors**: Specify what data to extract from pages

2. Example selectors:
   | Field Name | CSS Selector | Description |
   |------------|--------------|-------------|
   | title | h1 | Extract the main heading |
   | price | .product-price | Extract price elements |
   | description | .product-description | Extract product descriptions |
   | image_url | .product-image | Extract image URLs |
   | rating | .star-rating | Extract ratings |

3. Click "Start Crawling" to begin the crawl job

### Monitoring Jobs

The "Jobs" page shows all crawl jobs with their status:
- **Running**: Currently active jobs
- **Completed**: Successfully finished jobs
- **Stopped**: Jobs that were manually stopped
- **Error**: Jobs that encountered errors

Click on a job to see detailed information about its progress and results.

### Exploring Data

The "Data" page allows you to browse and search the extracted data:
1. Filter by URL to focus on specific websites
2. Set the limit to control how many records are displayed
3. Export data to CSV or JSON format for further analysis

### Visualizing Results

The "Visualize" page provides charts and statistics about your crawled data:
- Domain distribution chart
- Crawl activity over time
- Key metrics about the crawled websites

## Command-Line Interface

The command-line interface (CLI) provides powerful tools for automation and scripting.

### Basic Usage

```
python cli.py [command] [options]
```

### Available Commands

- **crawl**: Start a new crawl job
  ```
  python cli.py crawl https://example.com --depth 3 --selenium
  ```

- **analyze**: Analyze data from a previously crawled domain
  ```
  python cli.py analyze example.com --output report.json
  ```

- **server**: Start the web server
  ```
  python cli.py server --port 8080 --debug
  ```

- **export**: Export crawled data
  ```
  python cli.py export data.csv --filter example.com --limit 500
  ```

### Examples

1. Crawl a website with specific selectors:
   ```
   python cli.py crawl https://example.com --depth 2 --selectors '{"title": "h1", "price": ".price"}'
   ```

2. Generate a report for a crawled website:
   ```
   python cli.py crawl https://example.com --report report.json
   ```

3. Export data to Excel format:
   ```
   python cli.py export data.xlsx --filter blog
   ```

## Advanced Configuration

The application can be customized by editing the `config.json` file. Key settings include:

### Database Configuration

By default, the application uses SQLite. To use MongoDB:

```json
{
  "db_type": "mongodb",
  "mongodb_connection": "mongodb://localhost:27017/",
  "mongodb_db_name": "crawler_data"
}
```

### Crawler Configuration

```json
{
  "default_max_depth": 5,
  "concurrent_requests": 10,
  "request_timeout": 15,
  "respect_robots_txt": true,
  "user_agent": "CustomWebCrawler/1.0"
}
```

### Server Configuration

```json
{
  "host": "0.0.0.0",
  "port": 8080,
  "debug": false
}
```

## Troubleshooting

### Common Issues

1. **Selenium not working**
   - Make sure Chrome is installed
   - For headless environments, use the Docker container which includes Chrome

2. **Database connection errors**
   - Check connection parameters in `config.json`
   - Verify that MongoDB is running (if using MongoDB)

3. **Crawling being blocked**
   - Try changing the user agent in `config.json`
   - Decrease concurrent requests to avoid triggering rate limits
   - Use Selenium which can bypass some blocking mechanisms

### Logs

Log files are stored in the `logs` directory. Check these files for detailed error information:
- `crawler_app.log`: Main application log
- `crawler.log`: Crawler-specific logs
- `scrapy.log`: Scrapy-specific logs (if using Scrapy)

### Getting Help

If you encounter any issues not covered in this guide, please:
1. Check the GitHub repository issues section
2. Submit a detailed bug report with steps to reproduce the issue