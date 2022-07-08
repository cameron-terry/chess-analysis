from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

def get_country_of_origin(opponent):
    opponent = opponent.lower()
    html = 'https://www.chess.com/member/{}'.format(opponent)
    req = Request(html, headers={'User-Agent': 'Mozilla/5.0'})
    opp_soup = BeautifulSoup(urlopen(req), 'html.parser')

    try:
        country_unparsed_str = str(opp_soup.find("div", {"class": "country-flags-component"})).split('v-tooltip=')[1]
        country_parsed_str = country_unparsed_str.split('>')[0].replace("\"", "").replace("'", "")

        return country_parsed_str
    except IndexError:
        print("Error on opponent: ", opponent)
