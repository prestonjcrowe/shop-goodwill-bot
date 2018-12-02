# For a mapping of terms to max prices, search shopgoodwill.com for each term
# and tweet each listing that is within the notifcation bounds and is below
# the maximum price.

import requests
import urllib
import twitter
import time
import os
import pytz
from unidecode import unidecode
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta 

SGW_TIMEZONE = pytz.timezone('America/Los_Angeles')
INTERVAL = timedelta(minutes=5)      # frequency of polling
TWEET_BOUNDS= [INTERVAL, INTERVAL*2] # tweet when remaining time within bounds
PRODUCTS = {
    "gamecube controller" : 20,
}
API = twitter.Api(consumer_key=os.environ['twitter_api_key'],
                  consumer_secret=os.environ['twitter_api_secret'],
                  access_token_key=os.environ['twitter_access_key'],
                  access_token_secret=os.environ['twitter_access_secret'])

def main():
    for product in PRODUCTS:
        get_results(product, PRODUCTS[product])

def get_results(term, lim):
    print('Results for: {}'.format(term))
    url = ('https://www.shopgoodwill.com/Listings?st={}'.format(urllib.quote(term)) +
           '&sg=&c=&s=&lp=0&hp=999999&sbn=false&spo=false&snpo=f' +
           'alse&socs=false&sd=false&sca=false&caed=11/14/2018&c' +
           'adb=7&scs=false&sis=false&col=0&p=1&ps=40&desc=false' +
           '&ss=0&UseBuyerPrefs=true')
    
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    products = soup.find_all('span', {'class' : 'data-container'})

    for product in products:
        price = product.find('div', {'class' : 'price' }).text.split(' ')[0].strip()[1:]
        listing = product.find('div', {'class' : 'title' }).text.strip().split('\n')[0].strip()
        product_id = product.find('div', {'class' : 'product-number' }).text.split(' ')[2]
        url = 'https://www.shopgoodwill.com/Item/{}'.format(product_id)
        listing = product.find('div', {'class' : 'title' }).text.strip().split('\n')[0].strip()

        ends = product.select('div.timer.countdown-classic.product-countdown')[0]['data-countdown']
        end_date = SGW_TIMEZONE.localize(datetime.strptime(ends, '%m/%d/%Y %I:%M:%S %p'))
        durr = end_date - datetime.now(SGW_TIMEZONE)
        listing = unidecode(listing)

        print_listing(price, durr, listing, lim)
        if durr > TWEET_BOUNDS[0] and durr < TWEET_BOUNDS[1] and float(price) <= lim:
            tweet_listing(price, durr, listing, url)
            print("TWEETED!")

def print_listing(price, durr, listing, lim):
    if float(price) <= lim and durr <= TWEET_BOUNDS[1]:
        green('{: >10} | {: >22} | {: >20}'.format(float(price), durr, listing))
    elif float(price) <= lim:
        warning('{: >10} | {: >22} | {: >20}'.format(float(price), durr, listing))

def green(s):
    print('{}{}{}'.format('\033[92m', s, '\033[0m'))

def warning(s):
    print('{}{}{}'.format('\033[91m', s, '\033[0m'))

def tweet_listing(price, durr, listing,url):
    try:
        status = API.PostUpdate('SHOP GOODWILL BOT\n${} | {} | {} remaining\n{}'.format(price, listing, durr,url))
    except Exception as e:
        print('Could not post tweet - {}'.format(e))
    time.sleep(5)

if __name__ == '__main__':
    main()
