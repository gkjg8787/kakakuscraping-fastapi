import re

from bs4 import BeautifulSoup


class SurugayaMakepure:
    def __init__(self):
        self.shopdict :dict[str, dict]= {}

    def parse(self, htmltext, insert_proc_type :int | None = None):
        self.soup = BeautifulSoup(htmltext,"html.parser")
        self.shopdict = self.parseShop(insert_proc_type)
    
    def parseShop(self, insert_proc_type :int | None = None):
        res :dict[str, dict] = {}
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
            dic['url'] = u['href']
            dic['shop_id'] = m.group(1)
            if insert_proc_type:
                dic['insert_proc_type'] = insert_proc_type
            res[u.text] = dic
        return res

    def getShopDict(self):
        return self.shopdict

