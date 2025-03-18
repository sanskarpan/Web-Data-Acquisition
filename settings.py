# settings.py (for Scrapy configuration)
BOT_NAME = 'crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 1

# Configure item pipelines
ITEM_PIPELINES = {
    'crawler.pipelines.DatabasePipeline': 300,
}

# Enable logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'