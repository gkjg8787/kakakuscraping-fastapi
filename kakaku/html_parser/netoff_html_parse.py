
import re
from html_parser import htmlparse
from bs4 import BeautifulSoup
from itemcomb import (
    postage_data as posd,
    prefecture,
)


DEFAULT_STORENAME = "ネットオフ"

class NetoffParse(htmlparse.ParseItems):
    def __init__(self, fp, id, date, url):
        self.soup = BeautifulSoup(fp, "html.parser", from_encoding='utf-8')
        self.iteminfo = htmlparse.ParseItemInfo()
        self.iteminfo.id = id
        self.iteminfo.timeStamp = date
        self.iteminfo.url = url
        self.iteminfo.storename = DEFAULT_STORENAME
        self.parseItem(self.soup, self.iteminfo)
        
    
    def parseItem(self, soup, iteminfo):
        iteminfo.isSuccess = self.parseSuccess(soup)
        if not iteminfo.isSuccess:
            return
        iteminfo.name = self.parseTitle(soup)
        if not self.existZaiko(soup):
            iteminfo.isSuccess = False
            return
        self.parsePrice(soup, iteminfo)
        self.parseOnSale(soup, iteminfo)
    
    def parseSuccess(self, soup):
        q = r'.titleArea'
        elem = soup.select(q)
        if len(elem) == 0:
            return True
        ptn = r'【現在ご利用いただけません】'
        if ptn in str(elem[0]):
            return False
        return True
    
    def existZaiko(self, soup):
        q = r'.iStock'
        elem = soup.select(q)
        if len(elem) == 0:
            return False
        return True
    
    def parseTitle(self, soup):
        q = r'.descriptionIn h2'
        elem = soup.select(q)
        ptn = r'<h2>(<span class="free_shipping_red">送料無料</span>)?\t\t([\s\S]+)(<span)'
        m = re.findall(ptn, self.trimStr(str(elem[0])))
        return m[0][1]
    
    def parsePrice(self, soup, iteminfo):
        q = r'.descriptionIn'
        elem = soup.select(q)
        #if not self.isUsed(elem): return
        iteminfo.usedPrice = int(self.getPrice(elem))
        iteminfo.taxin = self.getTaxin(elem)
    
    def isUsed(self, elem):
        #一律中古扱い
        return True
    
    def getPrice(self, elem):
        yen = r'.price_text2'
        pricetag = elem[0].select(yen)
        ptext = pricetag[0].text.replace(',','')
        ptn = r'[1-9][0-9]*'
        m = re.findall(ptn, ptext)
        return int(m[0])

    def getTaxin(self, elem):
        q = r'.price_text2 .price_text_small'
        tax = elem[0].select(q)
        for s in tax:
            if '(税込)' in s:
                return True
        
        return False
    
    def parseOnSale(self, soup, iteminfo):
        q = r'.itemInfo .sale_balloon'
        elem = soup.select(q)
        if len(elem) == 0:
            return
        iteminfo.onSale = True
        name = elem[0].select('p')
        iteminfo.saleName = name[0].text

    def getItems(self):
        return (self.iteminfo,)
    

class NetoffDeliveryParse:
    pos_list :list[htmlparse.ParseStorePostage]

    def __init__(self, fp):
        soup = BeautifulSoup(fp, "html.parser")
        self.pos_list = self.parse_delivery(soup)
    
    def get_ParseStorePostage(self):
        return self.pos_list
    
    def parse_delivery(self, soup :BeautifulSoup):
        results :list[htmlparse.ParseStorePostage] = []
        base = self.parse_basic_shipping_terms(soup)
        if base:
            results.append(base)
        surcharge_list = self.parse_delivery_surcharge(soup)
        if surcharge_list:
            results.extend(surcharge_list)
        return results
    
    def parse_delivery_surcharge(self, soup :BeautifulSoup) -> list[htmlparse.ParseStorePostage]:
        results :list[htmlparse.ParseStorePostage] = []
        li = soup.select_one("#\\31 0").find_next_sibling(r'div').select(r".h-text__ul-sub li")
        for l in li:
            text_list = l.text.split("\n")
            pref_list :list[str] = []
            for text in text_list:
                target_text = re.sub(r"\s", "", text)
                if "北海道・沖縄を除く" in target_text:
                    pref_list = []
                    for prefname in prefecture.PrefectureName.get_all_prefecturename():
                        if "北海道" == prefname or "沖縄県" in prefname:
                            continue
                        pref_list.append(prefname)
                    continue
                if "北海道" == target_text:
                    pref_list = ["北海道"]
                    continue
                if "沖縄" == target_text:
                    pref_list = ["沖縄県"]
                    continue
                m = re.findall(r"ご注文1件につき([1-9][0-9]+)円", target_text)
                if not m:
                    continue
                psp :htmlparse.ParseStorePostage = self.create_common_shipping_terms(int(m[0]))
                psp.set_prefectures(pref_list)
                results.append(psp)
        return results


    def parse_basic_shipping_terms(self, soup :BeautifulSoup) -> htmlparse.ParseStorePostage:
        target = soup.select_one("#\\30 3").find_next_sibling(r'div').select_one(r'p')
        target_text = target.text.strip().replace(",", "")
        m = re.findall(r"送料は([1-9][0-9]+)円", target_text)
        if not m:
            return None
        basic_psp = self.create_common_shipping_terms(int(m[0]))
        m = re.findall(r"([1-9][0-9]+)円(以上)の場合は送料(無料)", target_text)
        if not m:
            return basic_psp
        bopecls = posd.BoundaryOperator.get(jtext=m[0][1])
        if not bopecls or m[0][2] != "無料":
            return basic_psp
        bval = int(m[0][0])
        rbope = posd.ShippingTermsBoundary.reverse_operator(bopecls.operator)
        basic_psp.terms[0].boundary = posd.ShippingTermsBoundary.add_terms_to_boundary(
                boundary=basic_psp.terms[0].boundary,
                add_ope=rbope,
                add_val=bval
            )
        return basic_psp
        
    def create_common_shipping_terms(self, common_postage :int):
        psp = htmlparse.ParseStorePostage()
        psp.storename = DEFAULT_STORENAME
        ppt = htmlparse.ParsePostageTerms()
        ppt.boundary = posd.ShippingTermsBoundary.create_boundary_of_db(lower_ope="<=",
                                                                        lower_val=0
                                                                        )
        ppt.postage = common_postage
        psp.add_terms(ppt)
        return psp