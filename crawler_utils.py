# crawler_utils.py
import re
import logging
import hashlib
import os
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

def normalize_url(url):
    """
    Normalize a URL by removing fragments, defaulting to https if scheme is missing,
    and ensuring trailing slash for domain-only URLs.
    
    Args:
        url: The URL to normalize
        
    Returns:
        str: Normalized URL
    """
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Build normalized URL
    normalized = f"{parsed.scheme}://{parsed.netloc}"
    
    # Add path (with trailing slash if empty)
    if not parsed.path:
        normalized += '/'
    else:
        normalized += parsed.path
    
    # Add query parameters if present
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized

def get_domain(url):
    """
    Extract domain from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        str: Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc

def is_valid_url(url):
    """
    Check if a URL is valid.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def is_same_domain(url1, url2):
    """
    Check if two URLs have the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        bool: True if same domain, False otherwise
    """
    return get_domain(url1) == get_domain(url2)

def url_to_filename(url):
    """
    Convert a URL to a safe filename.
    
    Args:
        url: The URL to convert
        
    Returns:
        str: Safe filename
    """
    # Remove scheme and special characters
    filename = re.sub(r'^https?://', '', url)
    filename = re.sub(r'[^a-zA-Z0-9]', '_', filename)
    
    # Limit length
    if len(filename) > 100:
        # Use hash for long URLs
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{filename[:50]}_{url_hash}"
    
    return filename

def fetch_robots_txt(domain):
    """
    Fetch and parse robots.txt file for a domain.
    
    Args:
        domain: Domain to fetch robots.txt for
        
    Returns:
        dict: Dictionary with allowed and disallowed paths
    """
    robots_url = f"https://{domain}/robots.txt"
    allowed = []
    disallowed = []
    
    try:
        response = requests.get(robots_url, timeout=5)
        if response.status_code == 200:
            lines = response.text.split('\n')
            
            current_agent = None
            for line in lines:
                line = line.strip().lower()
                
                if line.startswith('user-agent:'):
                    agent = line[11:].strip()
                    if agent == '*' or agent == 'web-crawler':
                        current_agent = agent
                    else:
                        current_agent = None
                        
                elif current_agent and line.startswith('allow:'):
                    path = line[6:].strip()
                    allowed.append(path)
                    
                elif current_agent and line.startswith('disallow:'):
                    path = line[9:].strip()
                    if path:  # Ignore empty disallow
                        disallowed.append(path)
    
    except requests.RequestException as e:
        logger.warning(f"Could not fetch robots.txt for {domain}: {str(e)}")
    
    return {
        'allowed': allowed,
        'disallowed': disallowed
    }

def is_allowed_by_robots(url, robots_rules):
    """
    Check if a URL is allowed according to robots.txt rules.
    
    Args:
        url: URL to check
        robots_rules: Dictionary with allowed and disallowed paths
        
    Returns:
        bool: True if allowed, False otherwise
    """
    parsed = urlparse(url)
    path = parsed.path
    
    # Check if specifically allowed
    for allow_path in robots_rules.get('allowed', []):
        if path.startswith(allow_path):
            return True
    
    # Check if specifically disallowed
    for disallow_path in robots_rules.get('disallowed', []):
        if path.startswith(disallow_path):
            return False
    
    # Default to allowed
    return True

def download_file(url, output_dir='downloads'):
    """
    Download a file from a URL.
    
    Args:
        url: URL to download
        output_dir: Directory to save to
        
    Returns:
        str: Path to downloaded file or None if failed
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine filename
        filename = url.split('/')[-1]
        if not filename:
            filename = f"download_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Ensure filename is unique
        file_path = os.path.join(output_dir, filename)
        if os.path.exists(file_path):
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            file_path = os.path.join(output_dir, filename)
        
        # Download file
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded {url} to {file_path}")
        return file_path
        
    except (requests.RequestException, IOError) as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return None

def check_urls_parallel(urls, max_workers=10, timeout=5):
    """
    Check multiple URLs in parallel.
    
    Args:
        urls: List of URLs to check
        max_workers: Maximum number of parallel workers
        timeout: Request timeout in seconds
        
    Returns:
        dict: Dictionary with URL status
    """
    results = {}
    
    def check_url(url):
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return url, response.status_code, response.url
        except requests.RequestException:
            return url, 0, None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            url, status_code, final_url = future.result()
            results[url] = {
                'status_code': status_code,
                'accessible': 200 <= status_code < 400,
                'redirect': final_url != url if final_url else False,
                'final_url': final_url
            }
    
    return results

def extract_metadata(html_content):
    """
    Extract metadata from HTML content.
    
    Args:
        html_content: HTML content as string
        
    Returns:
        dict: Extracted metadata
    """
    from bs4 import BeautifulSoup
    
    metadata = {}
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        metadata['title'] = title_tag.get_text(strip=True)
    
    # Extract meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name', meta.get('property', '')).lower()
        content = meta.get('content')
        
        if name and content:
            metadata[name] = content
    
    # Extract canonical URL
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        metadata['canonical_url'] = canonical['href']
    
    return metadata

def detect_content_type(html_content):
    """
    Detect the type of content in an HTML page.
    
    Args:
        html_content: HTML content as string
        
    Returns:
        str: Content type (article, product, listing, etc.)
    """
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for e-commerce indicators
    price_patterns = [
        r'\$\d+(\.\d{2})?',
        r'€\d+(\.\d{2})?',
        r'£\d+(\.\d{2})?',
        r'\d+(\.\d{2})?\s*(USD|EUR|GBP)'
    ]
    
    for pattern in price_patterns:
        if re.search(pattern, html_content):
            # Check for multiple products
            product_elements = 0
            for tag in soup.find_all(['div', 'li']):
                for pat in price_patterns:
                    if re.search(pat, tag.get_text()):
                        product_elements += 1
                        if product_elements > 1:
                            return "product_listing"
            
            return "product_page"
    
    # Check for blog/article indicators
    if soup.find('article') or soup.find(class_=re.compile(r'article|post|blog')):
        return "article"
    
    # Check for listing pages
    if soup.find_all('li', limit=15) or soup.find_all(class_=re.compile(r'list|grid')):
        return "listing"
    
    # Default to generic
    return "generic"

def take_screenshot(url, output_path=None):
    """
    Take a screenshot of a webpage using Selenium.
    
    Args:
        url: URL to screenshot
        output_path: Path to save screenshot to
        
    Returns:
        str: Path to screenshot or None if failed
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        import time
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to the page
        driver.get(url)
        time.sleep(2)  # Allow page to load
        
        # Determine output path if not provided
        if not output_path:
            filename = url_to_filename(url) + '.png'
            output_dir = 'screenshots'
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
        
        # Take screenshot
        driver.save_screenshot(output_path)
        driver.quit()
        
        logger.info(f"Screenshot of {url} saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error taking screenshot of {url}: {str(e)}")
        return None

def generate_site_report(domain, data):
    """
    Generate a report about a crawled website.
    
    Args:
        domain: Domain of the website
        data: List of crawled data items
        
    Returns:
        dict: Report statistics
    """
    if not data:
        return {"error": "No data available"}
    
    # Initialize report
    report = {
        "domain": domain,
        "crawl_date": datetime.now().isoformat(),
        "pages_crawled": len(data),
        "content_types": {},
        "response_times": {
            "average": 0,
            "min": float('inf'),
            "max": 0
        },
        "status_codes": {},
        "errors": 0
    }
    
    # Analyze data
    total_response_time = 0
    content_types = {}
    status_codes = {}
    
    for item in data:
        # Count content types
        content_type = item.get('content_type', 'unknown')
        content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Track response times
        response_time = item.get('response_time')
        if response_time:
            total_response_time += response_time
            report["response_times"]["min"] = min(report["response_times"]["min"], response_time)
            report["response_times"]["max"] = max(report["response_times"]["max"], response_time)
        
        # Count status codes
        status = item.get('status_code')
        if status:
            status_codes[status] = status_codes.get(status, 0) + 1
            
        # Count errors
        if status and (status < 200 or status >= 400):
            report["errors"] += 1
    
    # Calculate averages
    if total_response_time > 0:
        report["response_times"]["average"] = total_response_time / len(data)
    if report["response_times"]["min"] == float('inf'):
        report["response_times"]["min"] = 0
    
    # Add to report
    report["content_types"] = content_types
    report["status_codes"] = status_codes
    
    return report