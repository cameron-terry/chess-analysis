from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

html = 'https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3'
req = Request(html, headers={'User-Agent': 'Mozilla/5.0'})
iso_soup = BeautifulSoup(urlopen(req), 'html.parser')

table = iso_soup.find("div", {"class": "plainlist"})

iso_soup_table = ""
for link in table:
       abbrev = link.find("span")
       if type(abbrev) != int:
              iso_soup_table += link.text

iso_soup_table = iso_soup_table.replace('\xa0\xa0', ',').split("\n")

with open('ISO_3166-1_alpha-3_codes.csv', 'w') as fp:
       fp.write('country,code' + '\n')
       for country in iso_soup_table:
              name = str(country.split(',')[1])
              code = str(country.split(',')[0])
              fp.write("{},{}\n".format(name, code))
