import logging
import time
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebCrawler:
    """A versatile web crawler that can handle both static and dynamic websites."""
    
    def __init__(self, database_manager=None, use_selenium=False, max_workers=5):
        """
        Initialize the crawler with optional components.
        
        Args:
            database_manager: Handler for database operations
            use_selenium: Whether to use Selenium for JavaScript-heavy sites
            max_workers: Maximum number of concurrent crawling threads
        """
        self.database_manager = database_manager
        self.use_selenium = use_selenium
        self.max_workers = max_workers
        self.visited_urls = set()
        
        # Configure Selenium if enabled
        if self.use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Set up the Selenium WebDriver with Chrome."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {str(e)}")
            self.use_selenium = False
    
    def _get_page_content(self, url):
        """
        Get the page content using either requests or Selenium based on configuration.
        
        Args:
            url: The URL to fetch
            
        Returns:
            tuple: (page_content, success_status)
        """
        try:
            if self.use_selenium:
                try:
                    self.driver.get(url)
                    # Wait for the page to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    # Let JavaScript execute
                    time.sleep(2)
                    page_content = self.driver.page_source
                    return page_content, True
                except (TimeoutException, WebDriverException) as e:
                    logger.error(f"Selenium error for {url}: {str(e)}")
                    # Fall back to requests
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        return response.text, True
                    else:
                        logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                        return None, False
            else:
                # Use requests for static sites
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    return response.text, True
                else:
                    logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                    return None, False
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None, False
    
    def extract_data(self, url, selectors):
        """
        Extract data from a URL using provided CSS selectors.
        
        Args:
            url: The URL to extract data from
            selectors: Dict of {data_field: css_selector}
            
        Returns:
            dict: Extracted data
        """
        content, success = self._get_page_content(url)
        if not success:
            return None
        
        data = {'url': url}
        soup = BeautifulSoup(content, 'html.parser')
        
        for field, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                # If multiple elements match, get their text content
                data[field] = [element.get_text(strip=True) for element in elements]
                # If only one element, return string instead of list
                if len(data[field]) == 1:
                    data[field] = data[field][0]
            else:
                data[field] = None
        
        # Store the extracted data if a database manager is provided
        if self.database_manager:
            self.database_manager.save_data(data)
        
        return data
    
    def extract_links(self, url, restrict_domain=True):
        """
        Extract all links from a webpage.
        
        Args:
            url: The URL to extract links from
            restrict_domain: Whether to restrict links to the same domain
            
        Returns:
            list: Extracted URLs
        """
        content, success = self._get_page_content(url)
        if not success:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        base_domain = urlparse(url).netloc if restrict_domain else None
        
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url, href)
            
            # Filter out non-HTTP(S) URLs and same-domain restriction if enabled
            if not full_url.startswith(('http://', 'https://')):
                continue
                
            if restrict_domain and urlparse(full_url).netloc != base_domain:
                continue
                
            links.append(full_url)
            
        return links
    
    def crawl(self, start_url, max_depth=3, selectors=None, restrict_domain=True):
        """
        Crawl a website starting from the given URL.
        
        Args:
            start_url: The starting URL
            max_depth: Maximum depth to crawl
            selectors: Dict of {data_field: css_selector} for data extraction
            restrict_domain: Whether to restrict crawling to the same domain
            
        Returns:
            list: All extracted data items
        """
        all_data = []
        to_visit = [(start_url, 0)]  # (url, depth)
        
        while to_visit:
            url, depth = to_visit.pop(0)
            
            # Skip if already visited or exceeded max depth
            if url in self.visited_urls or depth > max_depth:
                continue
                
            logger.info(f"Crawling: {url} (depth: {depth})")
            self.visited_urls.add(url)
            
            # Extract data if selectors are provided
            if selectors:
                data = self.extract_data(url, selectors)
                if data:
                    all_data.append(data)
            
            # If not at max depth, extract links and add to queue
            if depth < max_depth:
                links = self.extract_links(url, restrict_domain)
                for link in links:
                    if link not in self.visited_urls:
                        to_visit.append((link, depth + 1))
        
        return all_data
    
    def parallel_crawl(self, start_url, max_depth=3, selectors=None, restrict_domain=True):
        """
        Crawl a website in parallel using a thread pool.
        
        Args:
            start_url: The starting URL
            max_depth: Maximum depth to crawl
            selectors: Dict of {data_field: css_selector} for data extraction
            restrict_domain: Whether to restrict crawling to the same domain
            
        Returns:
            list: All extracted data items
        """
        all_data = []
        to_visit = [(start_url, 0)]  # (url, depth)
        visited_urls = set()
        
        def process_url(url_depth):
            url, depth = url_depth
            
            # Skip if exceeded max depth
            if depth > max_depth:
                return None
                
            logger.info(f"Crawling: {url} (depth: {depth})")
            
            # Extract data if selectors are provided
            data = None
            if selectors:
                data = self.extract_data(url, selectors)
            
            # If not at max depth, extract links
            new_urls = []
            if depth < max_depth:
                links = self.extract_links(url, restrict_domain)
                for link in links:
                    if link not in visited_urls:
                        visited_urls.add(link)
                        new_urls.append((link, depth + 1))
            
            return (data, new_urls)
        
        visited_urls.add(start_url)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while to_visit:
                # Process a batch of URLs
                batch = [to_visit.pop(0) for _ in range(min(self.max_workers, len(to_visit)))]
                results = executor.map(process_url, batch)
                
                for result in results:
                    if result:
                        data, new_urls = result
                        if data:
                            all_data.append(data)
                        to_visit.extend(new_urls)
        
        return all_data
    
    def close(self):
        """Clean up resources."""
        if self.use_selenium and hasattr(self, 'driver'):
            self.driver.quit()