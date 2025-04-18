import bs4
import requests
import csv


URL =  "https://www.google.com/search?q=Amazon%20Stock%20Price";
r = requests.get(URL)


soup = bs4.BeautifulSoup(r.content, 'html.parser')
print(soup.prettify())

def get_price(soup):
    price = soup.find('div', class_='BNeawe iBp4i AP7Wnd').text
    return price

print(get_price(soup))