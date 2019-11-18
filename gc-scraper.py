import scrapy

class GraphicsCardSpider(scrapy.Spider):
    name = "gc_spider"
    start_urls = ['https://www.theitdepot.com/products-Graphic+Cards_C45.html']

    def parse(self, response):
        PRODUCT_SELECTOR = '#grid-container .category-product .products .product'
        for product in response.css(PRODUCT_SELECTOR):
            NAME_SELECTOR = '.product-info.text-left h3 a::text'
            PRICE_SELECTOR = '.product-price .price::text'

            print("{:<100s} : Rs {:7,.0f}".format(product.css(NAME_SELECTOR).extract_first(), float(product.css(PRICE_SELECTOR).extract_first())))
