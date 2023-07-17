import re

from bs4 import BeautifulSoup


class SurugayaMakepure:
    def __init__(self):
        self.shoplist = []

    def parse(self, htmltext):
        self.soup = BeautifulSoup(htmltext,"html.parser")
        self.shoplist = self.parseShop()
    
    def parseShop(self):
        res = []
        ptn = r'https://www.suruga-ya.jp/shop/'
        rptn = r'https:\/\/www\.suruga-ya\.jp\/shop\/(.+)'
        q = r'.full-width a'
        urlo = self.soup.select(q)
        for u in urlo:
            dic = {}
            if not u.has_attr('href'):
                continue
            m = re.match(rptn, u['href'])
            if m == None:
                continue
            #if not ptn in u['href']:
            #    continue
            dic['shop_name'] = u.text
            dic['href'] = u['href']
            dic['shop_id'] = m.group(1)
            res.append(dic)
        return res

    def getShopList(self):
        return self.shoplist

