import requests
import json
import base64
import sys
import urllib
from selenium import webdriver
from time import sleep
import os
# https://developer.ebay.com/api-docs/static
#   /oauth-client-credentials-grant.html
#
# eBay "client credentials grant" workflow
# for general use, non-confidential data
userAccessToken = ''

clientId = ''
ruName = ''
isSandbox = True
apiDomain = 'api.sandbox.ebay.com'
signinDomain = 'signin.sandbox.ebay.com'


def main():
    init()


def b64Encode(strVal):
    valBytes = strVal.encode('utf-8')
    encodedBytes = base64.b64encode(valBytes)
    return encodedBytes.decode('utf-8')


def b64Credentials(clientSecret):
    credentials = clientId + ':' + clientSecret
    return b64Encode(credentials)


def buildApiUrl(path):
    return 'https://' + apiDomain + path


def buildSigninUrl(path):
    return 'https://' + signinDomain + path


def setRuName(redirectUrlName):
    global ruName
    ruName = redirectUrlName


def setClientId(id):
    global clientId
    clientId = id


def sandboxMode(newValue):
    global isSandbox
    isSandbox = newValue
    global apiDomain
    global signinDomain
    if isSandbox:
        apiDomain = 'api.sandbox.ebay.com'
        signinDomain = 'signin.sandbox.ebay.com'
    else:
        apiDomain = 'api.ebay.com'
        signinDomain = 'signin.ebay.com'


def requestClientCredentialsToken(clientSecret):
    url = buildApiUrl('/identity/v1/oauth2/token')
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + b64Credentials(clientSecret)
    }
    payload = {
        'grant_type': 'client_credentials',
        'redirect_uri': ruName,
        'scope': 'https://api.ebay.com/oauth/api_scope'
    }
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("ERROR: Failed to get access token: "
              + response.json()['errors'][0]['message'])


def requestUserAccessToken(clientSecret):
    global userAccessToken

    authCode = requestUserPermissionCode()
    return exchangePermissionsForAccessToken(
        authCode, clientSecret)


def setUserAccessToken(token):
    global userAccessToken
    userAccessToken = token


def requestUserPermissionCode():
    payload = {
        'client_id': clientId,
        'redirect_uri': ruName,
        'response_type': 'code',
        'scope': 'https://api.ebay.com/oauth/api_scope https://api.eb'
        'ay.com/oauth/api_scope/sell.marketing.readonly https://api.e'
        'bay.com/oauth/api_scope/sell.marketing https://api.ebay.com/'
        'oauth/api_scope/sell.inventory.readonly https://api.ebay.com'
        '/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/a'
        'pi_scope/sell.account.readonly https://api.ebay.com/oauth/ap'
        'i_scope/sell.account https://api.ebay.com/oauth/api_scope/se'
        'll.fulfillment.readonly https://api.ebay.com/oauth/api_scope'
        '/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.'
        'analytics.readonly'
    }

    res = requests.get(buildSigninUrl('/authorize'), params=payload)
    newToken = ''
    chromedriver = "./bin/chromedriver.exe"
    #os.environ["webdriver.chrome.driver"] = chromedriver
    driver = webdriver.Chrome(chromedriver)
    driver.get(res.url)
    while not newToken:
        currentUrl = driver.current_url
        if currentUrl:
            if 'code=' in currentUrl:
                newToken = urllib.parse.parse_qs(currentUrl)['code'][0]
                driver.quit()
                print('Permission granted!')
        sleep(0.5)
    return newToken


def exchangePermissionsForAccessToken(authCode, clientSecret):
    payload = {
        'grant_type': 'authorization_code',
        'code': authCode,
        'redirect_uri': ruName
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + b64Credentials(clientSecret)
    }
    res = requests.post(buildApiUrl('/identity/v1/oauth2/token'),
                        data=payload, headers=headers)
    return res.json()['access_token']


def search(params):
    headers = {
        'Authorization': 'Bearer ' + userAccessToken
    }
    response = requests.get(
        buildApiUrl('/buy/browse/v1/item_summary/search'),
        params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("ERROR: Failed search for '" + params.q + "': "
              + response.json()['errors'][0]['message'])


def getInventoryItems(limit=200, offset=0):
    # Max limit is 200
    headers = {
        'Authorization': 'Bearer ' + userAccessToken
    }
    response = requests.get(
        buildApiUrl('/sell/inventory/v1/inventory_item'), params={'limit': limit, 'offset': offset}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("ERROR: Failed to retreive inventory items: "
              + response.json()['errors'][0]['message'])


def isTokenGood(token):
    headers = {
        'Authorization': 'Bearer ' + token
    }
    res = requests.get(
        buildApiUrl('/sell/inventory/v1/inventory_item'), params={'limit': 1, 'offset': 0}, headers=headers)

    return res.status_code == 200


def deleteInventoryItem(skuStr):
    headers = {
        'Authorization': 'Bearer ' + userAccessToken
    }
    response = requests.delete(
        buildApiUrl('/sell/inventory/v1/inventory_item/' + skuStr), headers=headers)

    if response.status_code == 204:
        return True
    else:
        print("ERROR: Failed to remove inventory item '" + skuStr + "': "
              + response.json()['errors'][0]['message'])


def createOrReplaceInventoryItem(skuStr, listingObj):
    headers = {
        'Authorization': 'Bearer ' + userAccessToken,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Content-Language': 'en-US'
    }
    response = requests.put(buildApiUrl(
        '/sell/inventory/v1/inventory_item/' + skuStr),
        data=json.dumps(listingObj), headers=headers)

    if response.status_code == 204:
        return True
    else:
        print("ERROR! Failed to create/replace inventory item for '" + skuStr
              + "': " + response.json()['errors'][0]['message'])


def createOffer(offerObj):
    headers = {
        'Authorization': 'Bearer ' + userAccessToken,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Content-Language': 'en-US'
    }
    response = requests.post(buildApiUrl(
        '/sell/inventory/v1/offer'),
        data=json.dumps(offerObj), headers=headers)

    if response.status_code == 201:
        return response.json()["offerId"]
    else:
        print("WARNING! '" +
              offerObj["sku"] + "': " + response.json()['errors'][0]['message'])
        return response.json()['errors'][0]["parameters"][0]["value"]


def publishOffer(offerId):
    headers = {
        'Authorization': 'Bearer ' + userAccessToken
    }
    response = requests.post(
        buildApiUrl('/sell/inventory/v1/offer/' + offerId + '/publish'), headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("ERROR: Failed to publisher offer '" + offerId + "': "
              + response.json()['errors'][0]['message'])


def getAllInventoryItemSkus():
    response = getInventoryItems()
    skus = []
    if response:
        if "inventoryItems" in response:
            items = response["inventoryItems"]
            for item in items:
                skus.append(item["sku"])
    return skus


def deleteAllInventoryItems():
    for sku in getAllInventoryItemSkus():
        if deleteInventoryItem(sku):
            print("Removed listing for '" + sku + "'")


def loadUserAccessToken():
    global userAccessToken
    token = json.load(open('token.json', mode='r'))
    return token['userAccessToken']


def saveUserAccessToken(token):
    tokenDict = {
        'userAccessToken': token
    }
    json.dump(tokenDict, open('token.json', mode='w'))


def init():
    config = json.load(open('config.json'))
    sandboxMode(config['sandboxMode'])
    setRuName(config['ruName'])
    setClientId(config['clientId'])
    token = loadUserAccessToken()

    if not isTokenGood(token):
        print('User access token has expired, prompting for user permissions...')
        token = requestUserAccessToken(config['clientSecret'])
        saveUserAccessToken(token)

    setUserAccessToken(token)


if __name__ == '__main__':
    main()
