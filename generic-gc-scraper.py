from bs4 import BeautifulSoup
import urllib.request
import re
import locale
from colorama import Fore, Style
import hashlib
from pathlib import Path
import sys
import getopt

HIGHLIGHT = '\033[95m'
NORMAL = '\033[0m'

httpHeaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/70.0'
}

useCache = True

def makeCacheableHttpCall(request):
    responseContent = ''
    urlhash = hashlib.md5(request.full_url.encode("utf-8")).hexdigest()
    posthash = ''
    if request.data is not None:
        posthash = hashlib.md5(request.data).hexdigest()
    pageId = urlhash + posthash
    # get from cache
    cachedFile = Path(f'cache/{pageId}')
    if useCache and cachedFile.is_file():
        responseContent = cachedFile.read_bytes()
    else:
        responseContent = urllib.request.urlopen(request).read()
        cachedFile.write_bytes(responseContent)
    return responseContent

gpuTypes = [
    { 'name': "GT 710" },
    { 'name': "GT 730" },
    { 'name': "GT 1030" },
    { 'name': "GTX 1050 Ti" },
    { 'name': "GTX 1050" },
    { 'name': "GTX 1060 Ti" },
    { 'name': "GTX 1060" },
    { 'name': "GTX 1070 Ti" },
    { 'name': "GTX 1070" },
    { 'name': "GTX 1080 Ti" },
    { 'name': "GTX 1080" },
    { 'name': "GTX 1650 Super", 'alternativeRegex': [ re.compile(r"GTX.*1650\sSuper", re.IGNORECASE)]},
    { 'name': "GTX 1650", 'alternativeRegex': [ re.compile(r"GTX.*1650", re.IGNORECASE)]},
    { 'name': "GTX 1660 Ti" , 'alternativeRegex': [ re.compile(r"GTX.*1660.*\sTi\s", re.IGNORECASE)]},
    { 'name': "GTX 1660 Super", 'alternativeRegex': [ re.compile(r"GTX.*1660\sSuper", re.IGNORECASE)]},
    { 'name': "GTX 1660", 'alternativeRegex': [ re.compile(r"GTX.*1660", re.IGNORECASE)] },
    { 'name': "RTX 2060 Ti" },
    { 'name': "RTX 2060 Super", 'alternativeRegex': [ re.compile(r"RTX.*2060\sSuper", re.IGNORECASE)]},
    { 'name': "RTX 2060", 'alternativeRegex': [ re.compile(r"RTX.*2060", re.IGNORECASE)]},
    { 'name': "RTX 2070 Ti", 'alternativeRegex': [ re.compile(r"RTX.*2070.*\sTi\s", re.IGNORECASE)] },
    { 'name': "RTX 2070 Super", 'alternativeRegex': [ re.compile(r"RTX.*2070\sSuper", re.IGNORECASE)] },
    { 'name': "RTX 2070", 'alternativeRegex': [ re.compile(r"RTX.*2070", re.IGNORECASE)] },
    { 'name': "RTX 2080 Ti" },
    { 'name': "RTX 2080 Super" },
    { 'name': "RTX 2080" },
    { 'name': "RX 5700 XT" },
    { 'name': "RX 5700" },
    { 'name': "RX 470" },
    { 'name': "RX 550" },
    { 'name': "RX 560" },
    { 'name': "RX 570" },
    { 'name': "RX 580" },
    { 'name': "RX 590" },
    { 'name': "RX Vega 64" },
    { 'name': "Vega Frontier" },
    { 'name': "R5 230" },
    { 'name': "P1000" },
    { 'name': "P2000" },
    { 'name': "P4000" },
    { 'name': "P600" },
    { 'name': "P400" },
    { 'name': "P620" },
    { 'name': "K420" },
    { 'name': "W5100" },
    { 'name': "NVS510" }
]

preferredGpuTypes = [
    'GTX 1660 Ti',
    'GTX 1660 Super',
    'GTX 1660',
    'GTX 1650'
]

gpuPriceRanges = {}
prices = {}
    
def makeComparable(string):
    return string.upper().replace(" ", "")

def extractGPUType(gpuName):
    for gpuType in gpuTypes:
        if makeComparable(gpuType['name']) in makeComparable(gpuName):
            return gpuType['name']
        if 'alternativeMatches' in gpuType:
            for alternative in gpuType['alternativeMatches']:
                if makeComparable(alternative) in makeComparable(gpuName):
                    return gpuType['name']
        if 'alternativeRegex' in gpuType:
            for regex in gpuType['alternativeRegex']:
                if regex.search(gpuName) is not None:
                    return gpuType['name']
    return "Uncategorized"

def addPriceToGPU(name, price, site):
    gpuType = extractGPUType(name)
    if gpuType not in gpuPriceRanges:
         gpuPriceRanges[gpuType] = {}
    if 'minPrice' not in gpuPriceRanges[gpuType]:
        gpuPriceRanges[gpuType]['minPrice'] = price
    if gpuPriceRanges[gpuType]['minPrice'] > price:
        gpuPriceRanges[gpuType]['minPrice'] = price
    if 'maxPrice' not in gpuPriceRanges[gpuType]:
        gpuPriceRanges[gpuType]['maxPrice'] = price
    if gpuPriceRanges[gpuType]['maxPrice'] < price:
        gpuPriceRanges[gpuType]['maxPrice'] = price
    
    if gpuType not in prices:
        prices[gpuType] = []
    prices[gpuType].append({'name': name, 'price': price, 'site': site})

def findProductsInPage(content, site):
    page = BeautifulSoup(content, features="lxml")
    products = page.select(sitePropertyMap[site]['selectors']['product'])

    for product in products:
        productName = product.select(sitePropertyMap[site]['selectors']['productName'])[0].string
        productPrice = extractPrice(product, site, sitePropertyMap[site]['selectors']['productPrice'])
        if productPrice == 0:
            try:
                if 'alternatePrice' in sitePropertyMap[site]['selectors']:
                    productPrice = extractPrice(product, site, sitePropertyMap[site]['selectors']['alternatePrice'])
            except ValueError:
                pass
        if productPrice != 0:
            addPriceToGPU(productName, productPrice, sitePropertyMap[site]['name'])

def extractPrice(product, site, selector):
    productPrice = 0
    productPriceElements = product.select(selector)
    if len(productPriceElements) > 0 and productPriceElements[0] is not None:
        productPriceString = productPriceElements[0].text
        if productPriceString is not None:
            productPrice = float(productPriceString.strip().replace('₹','').replace(',',''))
    return productPrice


def getPageCount(site):
    url = sitePropertyMap[site]['firstPageURL']
    content = makeCacheableHttpCall(urllib.request.Request(url, headers=httpHeaders))
    page = BeautifulSoup(content, features="lxml")
    pageLinks = page.select(sitePropertyMap[site]['selectors']['pageLinks'])
    return sitePropertyMap[site]['pageCountFunction'](pageLinks)

def getPageCountInMDComp(pageLinks):
    lastPage = 1
    for link in pageLinks:
        queryParams = link['href'].split('?')[1].split('&')
        for param in queryParams:
            [key, value] = param.split('=')
            if key == 'page':
                pageNo = int(value)
                if lastPage < pageNo:
                    lastPage = pageNo
    
    return lastPage

def getPageCountInITDepot(pageLinks):
    lastPage = 1
    for link in pageLinks:
        if 'id' in link.attrs:
            try:
                linkId = link['id']
                if (linkId is not None) and int(linkId):
                    pageNo = int(linkId)
                    if lastPage < pageNo:
                        lastPage = pageNo
            except ValueError:
                pass
    return lastPage

def getPageCountInPrimeAbgb(pageLinks):
    lastPage = 1
    for link in pageLinks:
        try:
            pageNo = int(link.string)
            if lastPage < pageNo:
                lastPage = pageNo
        except ValueError:
            pass
    return lastPage

def getPageCountInVedant(pageLinks):
    lastPage = 1
    for link in pageLinks:
        queryParams = link['href'].split('?')[1].split('&')
        for param in queryParams:
            [key, value] = param.split('=')
            if key == 'page':
                pageNo = int(value)
                if lastPage < pageNo:
                    lastPage = pageNo
    
    return lastPage

#findProductsInPage(content)

def callPage(pageNo, site, lastPage):
    return sitePropertyMap[site]['callPageFunction'](pageNo, site, lastPage)

def makeGetCall(pageNo, site, lastPage):
    paginatedURLTemplate = sitePropertyMap[site]['paginatedURLTemplate']
    url = paginatedURLTemplate.format(pageNo)
    paginatedContent = makeCacheableHttpCall(urllib.request.Request(url, headers=httpHeaders))
    return paginatedContent

def callPageInITDepot(pageNo, site, lastPage):
    paginatedURL = "https://www.theitdepot.com/category_filter.php"

    postAttributes = { 'categoryname' : 'Graphic+Cards',
    'filter-limit' : '12',
    'filter-orderby' : 'price_asc',
    'filter_listby' : 'Grid',
    'brand_id' : '',
    'category' : '45',
    'subcategory' : '',
    'clearence' : '',
    'free_shipping' : '',
    'ctotal' : '4',
    'btotal' : '9',
    'pageno' : pageNo,
    'fftotal' : '',
    'total_pages' : lastPage,
    'PageScrollProcess' : 'No',
    'PageFinished' : 'No',
    'price_range' : '2208,121455',
    'feature_filter0' : '4',
    'feature_filter1' : '18',
    'feature_filter2' : '2',
    'feature_filter3' : '4',
    'feature_filter4' : '5',
    'filter' : 'true' }

    postData = urllib.parse.urlencode(postAttributes)
    postData = postData.encode("utf-8")

    paginatedContent = makeCacheableHttpCall(urllib.request.Request(paginatedURL, data=postData, headers=httpHeaders))
    return paginatedContent

sitePropertyMap = {
    'ITDepot': {
        'name': "IT Depot",
        'pageCountFunction': getPageCountInITDepot,
        'firstPageURL': 'https://www.theitdepot.com/products-Graphic+Cards_C45.html',
        'callPageFunction': callPageInITDepot,
        'selectors': {
            'pageLinks': '.pagination-container ul li a',
            'product': '#grid-container .category-product .products .product',
            'productName': '.product-info.text-left h3 a',
            'productPrice': '.product-price .price'
        }
    },
    'MDComp': {
        'name': "MD Computers",
        'pageCountFunction': getPageCountInMDComp,
        'firstPageURL': 'https://mdcomputers.in/index.php?route=product/search&sort=p.price&order=ASC&search=&category_id=86',
        'paginatedURLTemplate': "https://mdcomputers.in/index.php?route=product/search&category_id=86&page={:d}",
        'callPageFunction': makeGetCall,
        'selectors': {
            'pageLinks': 'ul.pagination li a',
            'product': 'div.product-layout .product-item-container',
            'productName': 'h4 a',
            'productPrice': 'div.price span.price-new'
        }
    },
    'PrimeAbgb': {
        'name': "Prime ABGB",
        'pageCountFunction': getPageCountInPrimeAbgb,
        'firstPageURL': 'https://www.primeabgb.com/buy-online-price-india/graphic-cards-gpu/?pa-_stock_status=instock&orderby=price',
        'paginatedURLTemplate': "https://www.primeabgb.com/buy-online-price-india/graphic-cards-gpu/page/{:d}/?pa-_stock_status=instock&orderby=price",
        'callPageFunction': makeGetCall,
        'selectors': {
            'pageLinks': 'ul.page-numbers li .page-numbers',
            'product': 'ul.products li.product-item',
            'productName': '.product-innfo h3.product-name a',
            'productPrice': '.product-innfo .price ins .amount'
        }
    },
    'VedantComp': {
        'name': 'Vedant Computers',
        'pageCountFunction': getPageCountInVedant,
        'firstPageURL': "https://www.vedantcomputers.com/index.php?route=module/journal2_super_filter/products&module_id=282&filters=%2Favailability%3D1%2Fsort%3Dp.price%2Forder%3DASC%2Flimit%3D50&oc_route=product%2Fcategory&path=65&full_path=96_65&manufacturer_id=&search=&tag=",
        'paginatedURLTemplate': "https://www.vedantcomputers.com/index.php?route=module/journal2_super_filter/products&module_id=282&filters=availability%3D1%2Fsort%3Dp.price%2Forder%3DASC%2Flimit%3D50%2Fpage%3D{:d}&oc_route=product%2Fcategory&path=65&full_path=96_65&manufacturer_id=&search=&tag=",
        'callPageFunction': makeGetCall,
        'selectors': {
            'pageLinks': 'div.pagination div.links ul li a',
            'product': 'div.main-products div.product-details',
            'productName': 'h4.name a',
            'productPrice': '.price .price-new',
            'alternatePrice': '.price'
        }
    }
}

# lastPage = getPageCount('VedantComp')

# for pageNo in range(1, lastPage+1):
#     paginatedContent = callPage(pageNo, 'VedantComp')
#     findProductsInPage(paginatedContent, 'VedantComp')

try:
    options, args = getopt.getopt(sys.argv[1:], "c", ["cache="])
    for name, value in options:
        if name in ('-c', '--cache'):
            if value == 'false':
                useCache = False
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"

for site in sitePropertyMap:
    try:
        lastPage = getPageCount(site)

        for pageNo in range(1, lastPage+1):
            paginatedContent = callPage(pageNo, site, lastPage)
            findProductsInPage(paginatedContent, site)
    except:
        print("Got error while parsing {:s}".format(site['name']))

textToHighlight = [
    {'text': 'Super', 'style': Style.BRIGHT + Fore.BLUE},
    {'text': ' Ti ', 'pattern': r'\sTi\s', 'style': Style.BRIGHT + Fore.BLUE},
    {'text': ' Ex ', 'pattern': r'\sEx\s', 'style': Fore.YELLOW},
]

def highlightSomeText(text):
    highlightedText = text
    lengthBeforeHighlight = len(highlightedText)
    padding = 0
    for text in textToHighlight:
        pattern = text['text']
        if 'pattern' in text:
            pattern = text['pattern']
        highlightedText = re.sub(pattern, text['style'] + text['text'] + Style.RESET_ALL, highlightedText, flags=re.IGNORECASE)
    lengthAfterHighlight = len(highlightedText)
    padding += lengthAfterHighlight - lengthBeforeHighlight
    return highlightedText, padding

for gpuType in sorted(prices):
    print(gpuType)
    for line in sorted(prices[gpuType], key = lambda k: k['price']):
        (hText, hPadding) = highlightSomeText(line['name'].strip()[:70])
        nameWidth = 70 + hPadding
        print("\t {:<{nameWidth}s}: Rs {:8,.0f} - {:s}".format(hText.strip()[:(nameWidth)], line['price'], line['site'], nameWidth=nameWidth))

print()

for gpu in sorted(gpuPriceRanges):
    template = "{:<20s}- Min: Rs {:8,.0f} ; Max: Rs {:8,.0f}"
    if gpu in preferredGpuTypes:
        template = Fore.GREEN + "{:<20s}- Min: Rs {:8,.0f} ; Max: Rs {:8,.0f}" + Style.RESET_ALL
    print(template.format(
        gpu, gpuPriceRanges[gpu]['minPrice'], gpuPriceRanges[gpu]['maxPrice'])
        )

print(f'\nuseCache was {useCache}')