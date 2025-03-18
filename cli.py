# cli.py
import argparse
import logging
import sys
import json
import os

# Import our custom modules
from web_crawler import WebCrawler
from database_manager import DatabaseManager
from config import config
from crawler_utils import normalize_url, generate_site_report

def setup_logging(log_level="INFO"):
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.get("log_file", "crawler_cli.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )

def crawl_command(args):
    """
    Execute crawl command.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("crawl")
    
    logger.info(f"Starting crawl of {args.url} with depth {args.depth}")
    
    # Set up database connection
    db_type, connection_params = config.get_database_config()
    if args.output_format:
        # Override database type if output format is specified
        db_type = args.output_format
    
    db_manager = DatabaseManager(db_type=db_type, connection_params=connection_params)
    
    # Set up selectors
    selectors = {}
    if args.selectors:
        try:
            selectors = json.loads(args.selectors)
        except json.JSONDecodeError:
            logger.error("Invalid selectors format. Expected JSON.")
            sys.exit(1)
    
    # Initialize crawler
    crawler = WebCrawler(
        database_manager=db_manager,
        use_selenium=args.selenium,
        max_workers=args.workers
    )
    
    try:
        # Start crawling
        data = crawler.crawl(
            start_url=normalize_url(args.url),
            max_depth=args.depth,
            selectors=selectors,
            restrict_domain=not args.follow_external
        )
        
        logger.info(f"Crawl completed. Crawled {len(crawler.visited_urls)} pages.")
        
        # Generate report if requested
        if args.report:
            from urllib.parse import urlparse
            domain = urlparse(args.url).netloc
            report = generate_site_report(domain, data)
            
            # Save report
            report_path = args.report
            if report_path.lower() == 'true':
                report_path = f"report_{domain.replace('.', '_')}.json"
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to {report_path}")
        
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user.")
    except Exception as e:
        logger.error(f"Error during crawl: {str(e)}")
    finally:
        crawler.close()

def analyze_command(args):
    """
    Execute analyze command.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("analyze")
    
    logger.info(f"Analyzing data for {args.domain}")
    
    # Set up database connection
    db_type, connection_params = config.get_database_config()
    db_manager = DatabaseManager(db_type=db_type, connection_params=connection_params)
    
    # Get data
    data = db_manager.get_data(url=args.domain, limit=10000)
    
    if not data:
        logger.error(f"No data found for domain: {args.domain}")
        sys.exit(1)
    
    # Generate report
    report = generate_site_report(args.domain, data)
    
    # Save or print report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Analysis report saved to {args.output}")
    else:
        # Print report to console in a readable format
        print(f"\n===== Analysis Report for {args.domain} =====")
        print(f"Total pages crawled: {report['pages_crawled']}")
        print(f"Crawl date: {report['crawl_date']}")
        
        print("\nContent Types:")
        for content_type, count in report['content_types'].items():
            print(f"  - {content_type}: {count}")
        
        print("\nResponse Times:")
        for key, value in report['response_times'].items():
            print(f"  - {key}: {value:.2f}s")
        
        print("\nStatus Codes:")
        for status, count in report['status_codes'].items():
            print(f"  - {status}: {count}")
        
        print(f"\nErrors: {report['errors']}")
        print("==========================================\n")

def server_command(args):
    """
    Execute server command.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("server")
    
    # Import Flask app
    try:
        from app import app
    except ImportError:
        logger.error("Failed to import Flask application")
        sys.exit(1)
    
    # Update config if needed
    if args.host:
        config.set("host", args.host)
    if args.port:
        config.set("port", args.port)
    if args.debug is not None:
        config.set("debug", args.debug)
    
    # Start server
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 5000)
    debug = config.get("debug", False)
    
    logger.info(f"Starting web server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

def export_command(args):
    """
    Execute export command.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("export")
    
    logger.info(f"Exporting data to {args.output}")
    
    # Set up database connection
    db_type, connection_params = config.get_database_config()
    db_manager = DatabaseManager(db_type=db_type, connection_params=connection_params)
    
    # Get data
    url_filter = args.filter if args.filter else None
    limit = args.limit
    
    data = db_manager.get_data(url=url_filter, limit=limit)
    
    if not data:
        logger.error(f"No data found to export")
        sys.exit(1)
    
    # Determine export format
    format_ext = os.path.splitext(args.output)[1].lower()
    
    if format_ext == '.csv':
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(args.output, index=False)
    elif format_ext == '.json':
        with open(args.output, 'w') as f:
            json.dump(data, f, indent=2)
    elif format_ext == '.xlsx':
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_excel(args.output, index=False)
    else:
        logger.error(f"Unsupported export format: {format_ext}")
        sys.exit(1)
    
    logger.info(f"Exported {len(data)} records to {args.output}")

def screenshot_command(args):
    """
    Execute screenshot command.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("screenshot")
    
    logger.info(f"Taking screenshot of {args.url}")
    
    # Import utility function
    from crawler_utils import take_screenshot
    
    # Determine output path
    output_path = args.output
    if not output_path:
        # Generate default output path
        from crawler_utils import url_to_filename
        filename = url_to_filename(args.url) + '.png'
        output_dir = 'screenshots'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
    
    # Take screenshot
    try:
        screenshot_path = take_screenshot(args.url, output_path)
        if screenshot_path:
            logger.info(f"Screenshot saved to {screenshot_path}")
        else:
            logger.error("Failed to take screenshot")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        sys.exit(1)

def download_command(args):
    """
    Execute download command.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("download")
    
    from crawler_utils import download_file
    
    # Create output directory
    output_dir = args.output_dir or 'downloads'
    os.makedirs(output_dir, exist_ok=True)
    
    # Download single URL or URL list
    if args.url:
        urls = [args.url]
    elif args.url_file:
        try:
            with open(args.url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except IOError as e:
            logger.error(f"Error reading URL file: {str(e)}")
            sys.exit(1)
    else:
        logger.error("Either URL or URL file must be specified")
        sys.exit(1)
    
    # Download files
    success_count = 0
    for url in urls:
        logger.info(f"Downloading {url}")
        file_path = download_file(url, output_dir)
        if file_path:
            success_count += 1
    
    logger.info(f"Downloaded {success_count} of {len(urls)} files to {output_dir}")

def config_command(args):
    """
    Execute config command.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("config")
    
    # Get or set config
    if args.get:
        value = config.get(args.get)
        print(f"{args.get}: {value}")
    elif args.set and args.value:
        # Try to parse value as JSON first
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            # If not valid JSON, use as string
            value = args.value
        
        success = config.set(args.set, value)
        if success:
            logger.info(f"Set {args.set} to {value}")
        else:
            logger.error(f"Failed to set {args.set}")
            sys.exit(1)
    elif args.show:
        # Print full configuration
        print(json.dumps(config.to_dict(), indent=2))
    else:
        logger.error("No valid config operation specified")
        sys.exit(1)

def validate_command(args):
    """
    Execute validate command to check if a URL or set of URLs is valid and accessible.
    
    Args:
        args: Command line arguments
    """
    setup_logging(args.log_level)
    logger = logging.getLogger("validate")
    
    from crawler_utils import check_urls_parallel, is_valid_url
    
    # Get URLs to validate
    urls = []
    if args.url:
        urls = [args.url]
    elif args.url_file:
        try:
            with open(args.url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except IOError as e:
            logger.error(f"Error reading URL file: {str(e)}")
            sys.exit(1)
    else:
        logger.error("Either URL or URL file must be specified")
        sys.exit(1)
    
    # Validate URLs
    logger.info(f"Validating {len(urls)} URLs...")
    
    # First check URL format
    invalid_format = []
    valid_urls = []
    for url in urls:
        if not is_valid_url(url):
            invalid_format.append(url)
        else:
            valid_urls.append(url)
    
    if invalid_format:
        logger.warning(f"Found {len(invalid_format)} URLs with invalid format")
        if args.verbose:
            for url in invalid_format:
                print(f"Invalid format: {url}")
    
    # Then check accessibility
    if valid_urls:
        results = check_urls_parallel(valid_urls, max_workers=args.workers, timeout=args.timeout)
        
        accessible = [url for url, result in results.items() if result['accessible']]
        redirects = [url for url, result in results.items() if result['redirect']]
        errors = [url for url, result in results.items() if not result['accessible']]
        
        print(f"\n===== URL Validation Results =====")
        print(f"Total URLs: {len(urls)}")
        print(f"Invalid format: {len(invalid_format)}")
        print(f"Accessible: {len(accessible)}")
        print(f"Redirects: {len(redirects)}")
        print(f"Errors/Not accessible: {len(errors)}")
        
        if args.verbose:
            if redirects:
                print("\nRedirects:")
                for url in redirects:
                    print(f"  {url} -> {results[url]['final_url']}")
            
            if errors:
                print("\nErrors/Not accessible:")
                for url in errors:
                    print(f"  {url} (Status code: {results[url]['status_code']})")
        
        # Save results if output specified
        if args.output:
            output = {
                "summary": {
                    "total": len(urls),
                    "invalid_format": len(invalid_format),
                    "accessible": len(accessible),
                    "redirects": len(redirects),
                    "errors": len(errors)
                },
                "invalid_format": invalid_format,
                "results": results
            }
            
            with open(args.output, 'w') as f:
                json.dump(output, f, indent=2)
            
            logger.info(f"Validation results saved to {args.output}")

def main():
    """
    Main entry point for CLI.
    """
    parser = argparse.ArgumentParser(description="Web Crawler Command Line Interface")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default="INFO", help="Set logging level")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a website")
    crawl_parser.add_argument("url", help="URL to start crawling from")
    crawl_parser.add_argument("--depth", type=int, default=3, help="Maximum crawl depth")
    crawl_parser.add_argument("--selenium", action="store_true", help="Use Selenium for JavaScript-heavy sites")
    crawl_parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers")
    crawl_parser.add_argument("--follow-external", action="store_true", help="Follow links to external domains")
    crawl_parser.add_argument("--selectors", help="JSON string of CSS selectors for data extraction")
    crawl_parser.add_argument("--output-format", choices=["sqlite", "mongodb", "csv", "json"],
                             help="Output format for crawled data")
    crawl_parser.add_argument("--report", help="Generate a report (provide filename or 'true')")
    crawl_parser.set_defaults(func=crawl_command)
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze crawled data")
    analyze_parser.add_argument("domain", help="Domain to analyze")
    analyze_parser.add_argument("--output", help="Output file for analysis report")
    analyze_parser.set_defaults(func=analyze_command)
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start web server")
    server_parser.add_argument("--host", help="Server host")
    server_parser.add_argument("--port", type=int, help="Server port")
    server_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    server_parser.set_defaults(func=server_command)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export crawled data")
    export_parser.add_argument("output", help="Output file (.csv, .json, .xlsx)")
    export_parser.add_argument("--filter", help="Filter by URL (contains)")
    export_parser.add_argument("--limit", type=int, default=1000, help="Maximum number of records to export")
    export_parser.set_defaults(func=export_command)
    
    # Screenshot command
    screenshot_parser = subparsers.add_parser("screenshot", help="Take a screenshot of a webpage")
    screenshot_parser.add_argument("url", help="URL to screenshot")
    screenshot_parser.add_argument("--output", help="Output file path")
    screenshot_parser.set_defaults(func=screenshot_command)
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download files from URLs")
    download_group = download_parser.add_mutually_exclusive_group(required=True)
    download_group.add_argument("--url", help="URL to download")
    download_group.add_argument("--url-file", help="File containing URLs to download (one per line)")
    download_parser.add_argument("--output-dir", help="Output directory for downloaded files")
    download_parser.set_defaults(func=download_command)
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument("--get", help="Get a configuration value")
    config_group.add_argument("--set", help="Set a configuration value")
    config_group.add_argument("--show", action="store_true", help="Show all configuration")
    config_parser.add_argument("--value", help="Value to set (required with --set)")
    config_parser.set_defaults(func=config_command)
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate URLs")
    validate_group = validate_parser.add_mutually_exclusive_group(required=True)
    validate_group.add_argument("--url", help="URL to validate")
    validate_group.add_argument("--url-file", help="File containing URLs to validate (one per line)")
    validate_parser.add_argument("--output", help="Output file for validation results")
    validate_parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")
    validate_parser.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds")
    validate_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed results")
    validate_parser.set_defaults(func=validate_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    args.func(args)

if __name__ == "__main__":
    main()