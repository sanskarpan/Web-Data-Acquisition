# spider.py
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Join, MapCompose
import logging

class GenericItem(scrapy.Item):
    """Generic item that can hold any field."""
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    # This item will be dynamically expanded

class GenericSpider(CrawlSpider):
    """
    A configurable generic spider that can be used for multiple websites.
    """
    name = 'generic_spider'
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the spider with custom configuration.
        
        Expected kwargs:
            start_urls: List of URLs to start crawling from
            allowed_domains: List of domains to restrict crawling to
            follow_pattern: Regex pattern for URLs to follow
            page_pattern: Regex pattern for pages to extract data from
            item_selectors: Dict mapping item fields to CSS selectors
        """
        self.logger = logging.getLogger(self.name)
        
        # Set start_urls from kwargs
        self.start_urls = kwargs.get('start_urls', [])
        if not self.start_urls:
            self.logger.error("No start_urls provided")
            return

        # Set allowed domains from kwargs or extract from start_urls
        self.allowed_domains = kwargs.get('allowed_domains', [])
        if not self.allowed_domains:
            from urllib.parse import urlparse
            self.allowed_domains = [urlparse(url).netloc for url in self.start_urls]
            
        # Set follow and page patterns
        follow_pattern = kwargs.get('follow_pattern', '')
        page_pattern = kwargs.get('page_pattern', '')
        
        # Initialize rules
        rules = []
        if follow_pattern:
            rules.append(Rule(LinkExtractor(allow=follow_pattern), follow=True))
        if page_pattern:
            rules.append(Rule(LinkExtractor(allow=page_pattern), callback='parse_item'))
        
        # If no patterns provided, follow all links and parse all pages
        if not rules:
            rules.append(Rule(LinkExtractor(), callback='parse_item', follow=True))
            
        self.rules = rules
        
        # Set selectors for item extraction
        self.item_selectors = kwargs.get('item_selectors', {
            'title': 'title::text',
            'content': 'body p::text',
        })
        
        super().__init__(*args, **kwargs)
        
    def parse_item(self, response):
        """
        Parse the page and extract data according to the selectors.
        """
        loader = ItemLoader(item=GenericItem(), response=response)
        loader.default_output_processor = TakeFirst()
        
        # Add URL
        loader.add_value('url', response.url)
        
        # Add fields based on selectors
        for field, selector in self.item_selectors.items():
            # Handle special cases for certain fields
            if selector.endswith('::text'):
                selector_parts = selector.split('::')
                css_selector = selector_parts[0]
                
                # If we want to join multiple text elements
                if field == 'content':
                    loader.add_css(field, css_selector, Join('\n'))
                else:
                    loader.add_css(field, css_selector)
            else:
                # Default handling
                loader.add_css(field, selector)
                
        return loader.load_item()





# Run script
# -----------
# from scrapy.crawler import CrawlerProcess
# from scrapy.utils.project import get_project_settings
# 
# def run_scrapy_spider(db_manager, start_urls, allowed_domains=None, follow_pattern='', 
#                      page_pattern='', item_selectors=None):
#     """
#     Run a Scrapy spider with the given configuration.
#     
#     Args:
#         db_manager: DatabaseManager instance
#         start_urls: List of URLs to start crawling from
#         allowed_domains: List of domains to restrict crawling to
#         follow_pattern: Regex pattern for URLs to follow
#         page_pattern: Regex pattern for pages to extract data from
#         item_selectors: Dict mapping item fields to CSS selectors
#     """
#     process = CrawlerProcess(get_project_settings())
#     
#     process.crawl(
#         GenericSpider,
#         start_urls=start_urls,
#         allowed_domains=allowed_domains,
#         follow_pattern=follow_pattern,
#         page_pattern=page_pattern,
#         item_selectors=item_selectors,
#         db_manager=db_manager
#     )
#     
#     process.start()