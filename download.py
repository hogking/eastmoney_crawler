import requests
from lxml import etree

headers = {'Host':'guba.eastmoney.com',
                  'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'}

def get_html(link):
    r = requests.get(link, headers={'Host':'iguba.eastmoney.com', 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'}, timeout=10)
    return r.text

def load_page(link):
    try:
        r = requests.get(link, headers={'Host':'guba.eastmoney.com', 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'}, timeout=2)
        html = etree.HTML(r.text)
        return html
    except:
        print('获取%s失败' % link)