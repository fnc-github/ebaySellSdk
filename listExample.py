import ebay
import csv

ebay.init()

csvPath = 'ecom_combined.txt'
textFile = open("skusToList.txt", "r")
itemsToList = []
for text in textFile.readlines():
    itemsToList.append(text.replace("\n", "").lower())
textFile.close()


def readCsv(filename):
    csvFile = open(filename, "r")
    reader = csv.DictReader(csvFile, delimiter="	")
    rows = []
    for row in reader:
        rows.append(row)
    csvFile.close()
    return rows


def listContains(list, val):
    return any(val in s for s in list)


print("Loading csv...")
products = readCsv(csvPath)

filteredProducts = []
for row in products:
    if listContains(itemsToList, row['ITEM_A'].lower()):
        filteredProducts.append(row)

for product in filteredProducts:
    print("Posting listing for '" + product['ITEM_A'] + "'...")
    imageUrls = []
    imageIndex = 1
    while imageIndex < 6:
        imgUrl = product['IMGURL' + str(imageIndex)].replace(" ", "%20")
        if imgUrl == '':
            break
        imageUrls.append(imgUrl)
        imageIndex += 1
    bullets = []
    bulletIndex = 1
    while bulletIndex < 6:
        bullet = product['BULLET' + str(bulletIndex)]
        if bullet == '':
            break
        bullets.append(bullet)
        bulletIndex += 1
    inventoryItemObj = {
        "product": {
            "title": product['TITLE'],
            "aspects": {
                "Feature": bullets
            },
            "brand": product['BRAND'],
            "description": product['LONGDESC'],
            # Some numbers are in scientific notation
            "upc": [product['VUPC']],
            "imageUrls": imageUrls
        },
        "condition": "NEW",
        "packageWeightAndSize": {
            "weight": {
                "value": product['WEIGHT'],
                "unit": "POUND"
            }
        },
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 10
            }
        }
    }
    response = ebay.createOrReplaceInventoryItem(
        product['ITEM_A'], inventoryItemObj)
    if response:
        offerObj = {
            "sku": product['ITEM_A'],
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "availableQuantity": 10,
            "categoryId": "82290",  # cat id... yeahh...
            "listingDescription": product['LONGDESC'],
            "listingPolicies": {
                "fulfillmentPolicyId": "93190269015",
                "paymentPolicyId": "92837343015",
                "returnPolicyId": "92792976015"
            },
            "pricingSummary": {
                "price": {
                    "currency": "USD",
                    "value": product["APRICE"]
                }
            },
            "quantityLimitPerBuyer": 2
        }
        offerId = ebay.createOffer(offerObj)
        if offerId:
            if ebay.publishOffer(offerId):
                print("'" + product['ITEM_A'] + "' successfully posted!")
