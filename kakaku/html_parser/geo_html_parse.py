import re

from bs4 import BeautifulSoup

from html_parser import htmlparse
from itemcomb import postage_data as posd

DEFAULT_STORENAME = "ゲオ"

class GeoParse(htmlparse.ParseItems):
    def __init__(self, fp, id, date, url):
        self.soup = BeautifulSoup(fp, "html.parser", from_encoding='utf-8')
        self.iteminfo = htmlparse.ParseItemInfo()
        self.iteminfo.id = id
        self.iteminfo.timeStamp = date
        self.iteminfo.url = url
        self.iteminfo.storename = DEFAULT_STORENAME
        self.parseItem(self.soup, self.iteminfo)
        
    def parseItem(self, soup, iteminfo):
        iteminfo.isSuccess = self.existPage(soup)
        if not iteminfo.isSuccess:
            return
        iteminfo.name = self.parseTitle(soup)
        self.parsePrice(soup, iteminfo)
        self.parseSale(soup, iteminfo)
    
    def existPage(self, soup):
        q = r'.notice_ p'
        noto = soup.select(q)
        if len(noto) == 0:
            return True
        if '申し訳ございません' in noto[0].text:
            return False
        return True
    
    def parseTitle(self, soup):
        q = r'.goods_name_'
        elem = soup.select(q)
        title = str(elem[0].text).replace('\u3000', ' ')
        return title
    
    def parsePrice(self, soup, iteminfo):
        price = int(self.getPrice(soup))
        if price == -1:
            iteminfo.isSuccess = False
            return

        if self.isUsed(soup):
            iteminfo.usedPrice = price
        else:
            iteminfo.newPrice = price
        iteminfo.taxin = self.getTaxin(soup)
    
    def getPrice(self, soup):
        if not self.isZaiko(soup):
            return -1
        q = r'.goods_price_ .goods_detail_price_'
        elem = soup.select(q)
        ptn = r'([1-9][0-9,]+)円'
        m = re.findall(ptn, self.trimStr(elem[0].text))
        if len(m) == 0:
            return -1
        price = m[0].replace(',', '')
        return price
    
    def isZaiko(self, soup):
        q = r'.cart_btn_list_ li img'
        elem = soup.select(q)
        if len(elem) == 0:
            return True
        for e in elem:
            if 'NoStock' in e['src']:
                return False
        return True
        
    def isUsed(self, soup):
        q = r'.goodsspec_ .icon_ .labelSituation'
        elem = soup.select(q)
        if '新品' in elem[0].text:
            return False

        if '状態' in elem[0].text:
            return True

        return False
    
    def getTaxin(self, soup):
        q = r'.goods_detail_price_ .tax_'
        tax = soup.select(q)
        for s in tax:
            if '税込' in s.text:
                return True
        
        return False
    
    def parseSale(self, soup, iteminfo):
        q = r'.goodsspec_ .icon1_ img'
        elem = soup.select(q)
        for e in elem:
            if 'sale.png' in e['src']:
                iteminfo.onSale = True
        
        if not iteminfo.onSale:
            return
        
        q = r'.goodsspec_ .goods_campaign_'
        elem = soup.select(q)
        if len(elem) == 0: return
        iteminfo.saleName = elem[0].text.replace('\u3000', ' ')

    def getItems(self):
        return (self.iteminfo,)
    
class GeoGuideParse:
    pos_list :list[htmlparse.ParseStorePostage]

    def __init__(self, fp):
        soup = BeautifulSoup(fp, "html.parser")
        self.pos_list = self.parse_guide(soup)
    
    def get_ParseStorePostage(self):
        return self.pos_list
    
    def parse_guide(self, soup :BeautifulSoup):
        p_list = soup.select_one("#id1").find_next_sibling("section").select("dd p")
        basic_postage :int | None = None
        boundary_val :int | None = None
        reverse_boundary_ope :int | None = None
        for p in p_list:
            target_text = re.sub("\s+", "", p.text.replace(",", ""))
            cw_m = re.findall(r"全国一律([1-9][0-9]+)円", target_text)
            if cw_m:
                basic_postage = int(cw_m[0])
                continue

            fs_m = re.findall(r"([1-9][0-9]+)円(以上).+で送料(無料)", target_text)
            if not fs_m:
                continue
            if not fs_m[0][0]\
                or not fs_m[0][1]\
                or not fs_m[0][2]:
                continue
            boundary_val = int(fs_m[0][0])
            reverse_boundary_ope = posd.ShippingTermsBoundary.reverse_operator("<=")
        if basic_postage is None:
            return None
        if not boundary_val:
            return [self.create_parsestorepostage(boundary_ope="<=",
                                                  boundary_val=0,
                                                  postage=basic_postage
                                                  )
                    ]
        psp = htmlparse.ParseStorePostage()
        psp.storename = DEFAULT_STORENAME
        ppt = htmlparse.ParsePostageTerms()
        ppt.boundary = posd.ShippingTermsBoundary.create_boundary_of_db(lower_ope="<=",
                                                                        lower_val=0,
                                                                        upper_ope=reverse_boundary_ope,
                                                                        upper_val=boundary_val
                                                                        )
        ppt.postage = basic_postage
        psp.add_terms(ppt)
        return [psp]
    
    def create_parsestorepostage(self, boundary_ope :str, boundary_val :int, postage :int):
        psp = htmlparse.ParseStorePostage()
        psp.storename = DEFAULT_STORENAME
        ppt = htmlparse.ParsePostageTerms()
        ppt.boundary = posd.ShippingTermsBoundary.create_boundary_of_db(lower_ope=boundary_ope,
                                                                        lower_val=boundary_val
                                                                        )
        ppt.postage = postage
        psp.add_terms(ppt)
        return psp
        
