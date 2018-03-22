import ebay
import csv

ebay.init()

csvPath = 'ecom_combined.txt'
skusFilePath = "skusToList.txt"

merchantLocationKey = '1'
merchantLocation = {
    "name": "ABC Store",
    "phone": "800-123-4567",
    "locationWebUrl": "https://abcstore.com",
    "locationInstructions": "Pick-up during business hours only.",
    "operatingHours": [
        {
            "intervals": [
                {
                    "open": "08:00:00",
                    "close": "16:30:00"
                }
            ],
            "dayOfWeekEnum": "MONDAY"
        },
        {
            "intervals": [
                {
                    "open": "08:00:00",
                    "close": "16:30:00"
                }
            ],
            "dayOfWeekEnum": "TUESDAY"
        },
        {
            "intervals": [
                {
                    "open": "08:00:00",
                    "close": "16:30:00"
                }
            ],
            "dayOfWeekEnum": "WEDNESDAY"
        },
        {
            "intervals": [
                {
                    "open": "08:00:00",
                    "close": "16:30:00"
                }
            ],
            "dayOfWeekEnum": "THURSDAY"
        },
        {
            "intervals": [
                {
                    "open": "08:00:00",
                    "close": "16:30:00"
                }
            ],
            "dayOfWeekEnum": "FRIDAY"
        }
    ],
    "merchantLocationKey": merchantLocationKey,
    "location": {
        "address": {
            "addressLine1": "1st St",
            "city": "New York",
            "stateOrProvince": "NY",
            "postalCode": "12345",
            "country": "US"
        },
        "geoCoordinates": {
            "latitude": 30.0,
            "longitude": -80.0
        }
    },
    "merchantLocationStatus": "ENABLED",
    "locationTypes": [
        "STORE",
        "WAREHOUSE"
    ]
}

listingPolicies = {
    "fulfillmentPolicyId": "93190269015",
    "paymentPolicyId": "92837343015",
    "returnPolicyId": "92792976015"
}

itemsToList = []
with open("skusToList.txt", "r") as skusFile:
    for text in skusFile.readlines():
        itemsToList.append(text.replace("\n", "").lower())
    print('{} sku{} read'.format(len(itemsToList), "s" if len(itemsToList) > 1 else ""))


def readCsv(filename):
    with open(filename, "r") as csvFile:
        reader = csv.DictReader(csvFile, delimiter="\t")
        rows = []
        for row in reader:
            rows.append(row)
        print('{} item{} read'.format(len(rows), "s" if len(rows) > 1 else ""))
        return rows

def listContains(list, val):
    return any(val in s for s in list)

def createInvtLoc(locationKey, locationDict):
    ebay.createInventoryLocation(locationKey, locationDict)

# Count locations, add if necessary
invtLocations = ebay.getInventoryLocations()
if (not len(invtLocations)):
    createInvtLoc(merchantLocationKey, merchantLocation)
 
# Start adding products
print("Loading csv...")
products = readCsv(csvPath)

# Filter products by desired skus
filteredProducts = []
for row in products:
    if listContains(itemsToList, row['ITEM_A'].lower()):
        filteredProducts.append(row)

# Create or replace inventory items,
# create & publish offers.
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
            "mpn": product['VPARTNO'],
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
            "merchantLocationKey": merchantLocationKey, # seller-defined location key
            "listingDescription": product['LONGDESC'],
            "listingPolicies": listingPolicies,
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
