from bs4 import BeautifulSoup
import urllib.request
import re

gpuTypes = [
    "GTX 1660 Ti",
    "GTX 1660",
    "GTX 1650",
    "RTX 2060 Ti",
    "RTX 2060 Super",
    "RTX 2060",
    "RTX 2070 Ti",
    "RTX 2070 Super",
    "RTX 2070",
    "RTX 2080 Ti",
    "RTX 2080 Super",
    "RTX 2080",
    "RX 5700 XT",
    "RX 5700",
    "RX 550",
    "RX 560",
    "RX 570",
    "RX 580",
    "RX 590"
]

gpuPriceRanges = {}
prices = {}
# for gpuType in gpuTypes:
#     gpuPriceRanges[gpuType] = { 'minPrice': 1000000, 'maxPrice': 0}
# gpuPriceRanges['Uncategorized'] = { 'minPrice': 1000000, 'maxPrice': 0}
    

def extractGPUType(gpuName):
    for gpuType in gpuTypes:
        if gpuType.upper() in gpuName.upper():
            return gpuType
    return "Uncategorized"

def addPriceToGPU(gpuType, name, price):
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
    prices[gpuType].append({'name': name, 'price': price})

def findProductsInPage(content):
    page = BeautifulSoup(content, features="lxml")
    products = page.select('#grid-container .category-product .products .product')

    for product in products:
           productName = product.select('.product-info.text-left h3 a')[0].string
           gpuType = extractGPUType(productName)
           productPrice = float(product.select('.product-price .price')[0].string)
           addPriceToGPU(gpuType, productName, productPrice)
           #print("{:<20s} : {:<80s} : Rs {:6,.0f}".format(gpuType, productName, productPrice))


def getPageCount():
    url = "https://www.theitdepot.com/products-Graphic+Cards_C45.html"

    content = urllib.request.urlopen(url).read()

    page = BeautifulSoup(content, features="lxml")
    pageLinks = page.select('.pagination-container ul li a')

    print("Number of page links found = {:d}".format(len(pageLinks)))

    pageNumbers = set()
    for link in pageLinks:
        #print(link)
        if 'id' in link.attrs:
            try:
                linkId = link['id']
                if (linkId is not None) and float(linkId):
                    pageNumbers.add(linkId)
            except ValueError:
                pass
    print()
    print(sorted(pageNumbers))
    lastPage = max([int(page) for page in pageNumbers])
    print(lastPage)
    return lastPage


#findProductsInPage(content)

def callPage(pageNo):
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
    'total_pages' : '8',
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

    paginatedContent = urllib.request.urlopen(urllib.request.Request(paginatedURL, postData)).read()
    return paginatedContent

lastPage = getPageCount()

for pageNo in range(1, lastPage+1):
    paginatedContent = callPage(pageNo)
    findProductsInPage(paginatedContent)

print()

for gpuType in prices:
    print(gpuType)
    for line in prices[gpuType]:
        print("\t {:<80s}: Rs {:10,.0f}".format(line['name'], line['price']))

print()

for gpu in sorted(gpuPriceRanges):
    print("{:<20s}- Min: Rs {:10,.0f} ; Max: Rs {:10,.0f}".format(
        gpu, gpuPriceRanges[gpu]['minPrice'], gpuPriceRanges[gpu]['maxPrice'])
        )
