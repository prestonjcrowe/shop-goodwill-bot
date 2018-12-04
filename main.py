# For a mapping of terms to max prices, search shopgoodwill.com for each term
# and send an email for each listing that is within the notifcation bounds and
# below its maximum price.
import smtplib
import requests
import urllib
import time
import os
import pytz
from unidecode import unidecode
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta 
from email.mime.text import MIMEText
import email.utils

SGW_TIMEZONE = pytz.timezone('America/Los_Angeles')
INTERVAL = timedelta(minutes=20)      # frequency of polling
NOTIFY_BOUND= [INTERVAL, INTERVAL*2]  # tweet when remaining time within bounds
EMAIL = os.environ['SENDMAIL_USERNAME']
PASSWORD = os.environ['SENDMAIL_PASSWORD']

PRODUCTS = {
    "gamecube controller" : 20,
    "thinkpad" : 20
}

def main():
    for product in PRODUCTS:
        get_results(product, PRODUCTS[product])

def get_results(term, lim):
    print('Looking for {}...'.format(term))
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

        ends = product.select('div.timer.countdown-classic.product-countdown')[0]['data-countdown']
        end_date = SGW_TIMEZONE.localize(datetime.strptime(ends, '%m/%d/%Y %I:%M:%S %p'))
        durr = end_date - datetime.now(SGW_TIMEZONE)
        listing = unidecode(listing)
        price = float(price)

        if (durr > NOTIFY_BOUND[0] and durr < NOTIFY_BOUND[1]):
            if price <= lim:
                print_listing(price, listing, durr, lim)
                send_email(price, listing, url, durr)

def print_listing(price, listing, durr, lim):
    print('{: >10} | {: >22} | {: >20}'.format(price, durr, listing))

def send_email(price, listing, url, durr):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465) 
    server.ehlo()  
    server.login(EMAIL,PASSWORD)

    msg = MIMEText(url + '\n' + str(durr) + 'remaining')
    msg['To'] = email.utils.formataddr(('Wiener Boy', EMAIL))
    msg['From'] = email.utils.formataddr(('SHOPGOODWILL', EMAIL))
    msg['Subject'] = '${} | {}'.format(price, listing)

    server.sendmail(EMAIL, EMAIL, msg.as_string())
    server.quit()

if __name__ == '__main__':
    main()
