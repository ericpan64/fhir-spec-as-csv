"""
Parses urls and saves lists to `input`
"""

from bs4 import BeautifulSoup
import requests

def get_resource_list(base_url):
    """ Returns list of html filenames """
    list_ext = 'resourcelist.html'
    page = requests.get(base_url + list_ext)
    soup = BeautifulSoup(page.content, 'html.parser')
    html_body = soup.find('body')
    body_tables = html_body.find_all('table')
    ul_tags = body_tables[1].find_all('ul')
    resource_list = [] # parsed list of individual resource html pages
    for ul in ul_tags:
        li_tags = ul.find_all('li')
        for li in li_tags:
            text = li.text[:-2].split(' ')[0] + '.html'
            resource_list.append(text)
    return resource_list

if __name__ == '__main__':
    # Parse resource lists urls for r4
    # Parse lists for CARIN BB
    # Parse lists for DaVinci?
    pass