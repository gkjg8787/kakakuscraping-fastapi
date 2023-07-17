
from typing import List, Dict, Optional
import re
import urllib

from common.filter_name import FilterQueryName, FilterDefault
from html_parser.search_parser import SearchCmn, SearchParser

from pydantic import BaseModel

class InnerItem(BaseModel):
    title :str = ""
    url :str = ""

class ItemPrice(BaseModel):
    price :str = ""
    price_tail_text :str = ""
    price_pre_text :str = ""

class MainItem(InnerItem):
    new :Optional[ItemPrice] = None
    used :Optional[ItemPrice] = None

class MakepureItem(InnerItem):
    price :str = ""
    biko :str = ""

class SearchResultItem(BaseModel):
    storename :str
    img :str
    img_on_err :str = ""
    title :str
    item_url :str
    category :str = ""
    state :Optional[str] = None
    sinagire :Optional[str] = None
    main :Optional[MainItem] = None
    makepure :Optional[MakepureItem] = None


class PageInfo(BaseModel):
    num : int
    url : Optional[str] = None
    cure_page :bool = False

class SearchResultPage(BaseModel):
    pages : List[PageInfo] = []
    pre_url :Optional[str] = None
    next_url :Optional[str] = None
    more_page :bool = False

class SearchResult(BaseModel):
    items :List[SearchResultItem] = []
    page :SearchResultPage = None

class SearchDictConverter:

    @classmethod
    def convertToSearchResult(cls, items :List, pageinfo :Dict, urlparam :Dict) -> SearchResult:
        items = cls.convertToSearchResultItems(items)
        page = cls.convertToSearchResultPage(pageinfo, urlparam)
        return SearchResult(items=items, page=page)

    @classmethod
    def convertToSearchResultPage(cls, pageinfo :Dict, urlparam :Dict) -> SearchResultPage:
        srp = SearchResultPage()
        pages :List[PageInfo] = []
        current_page_num = None
        if SearchCmn.CURRENT in pageinfo:
            current_page_num = int(pageinfo[SearchCmn.CURRENT])

        if SearchParser.MIN in pageinfo and SearchParser.MAX in pageinfo:
            for i in range(pageinfo[SearchParser.MIN], pageinfo[SearchParser.MAX]+1):
                pi = PageInfo(num=i, url=cls.createURLParam(urlparam, i))
                if current_page_num and i == current_page_num:
                    pi.cure_page = True
                pages.append(pi)

        if SearchParser.MIN in pageinfo \
            and current_page_num \
            and int(pageinfo[SearchParser.MIN]) != current_page_num:
            srp.pre_url = cls.createURLParam(urlparam, current_page_num-1)
        if SearchParser.MAX in pageinfo \
            and current_page_num \
            and int(pageinfo[SearchParser.MAX]) != current_page_num:
            srp.next_url = cls.createURLParam(urlparam, current_page_num+1)
        if SearchParser.MOREPAGE in pageinfo and pageinfo[SearchParser.MOREPAGE] == SearchCmn.TRUE:
            srp.more_page = True
        
        srp.pages = pages
        return srp
    
    @classmethod
    def createURLParam(cls, urlparam, num):
        uparam = { FilterQueryName.PAGE.value : num }
        if FilterQueryName.WORD.value in urlparam:
            uparam[FilterQueryName.WORD.value] = urlparam[FilterQueryName.WORD.value]
        if SearchParser.CATEGORY in urlparam:
            uparam[FilterQueryName.CATEGORY.value] = urlparam[SearchParser.CATEGORY]
        if FilterQueryName.STORE.value in urlparam:
            uparam[FilterQueryName.STORE.value] = urlparam[FilterQueryName.STORE.value]
        if FilterQueryName.SAFES.value in urlparam:
            uparam[FilterQueryName.SAFES.value] = urlparam[FilterQueryName.SAFES.value]
        if SearchParser.ZAIKO in urlparam:
            uparam[FilterQueryName.ZAIKO.value] = urlparam[SearchParser.ZAIKO]

        return '?' + str( urllib.parse.urlencode(uparam,True) )
    
    
    @classmethod
    def convertToSearchResultItems(cls, items :List[Dict]):
        results :List[SearchResultItem] = []
        for item in items:
            sri = SearchResultItem(storename=item[SearchParser.STORENAME],
                                   img=item[SearchParser.IMAGE_URL],
                                   title=item[SearchParser.TITLE],
                                   item_url=item[SearchParser.TITLE_URL],
                                   )
            if SearchParser.MAKEPURE in item and item[SearchParser.MAKEPURE]:
                sri.makepure = cls.convertMakepureItem(item)
            maini = cls.convertMainItem(item)
            if maini:
                sri.main = maini
            if SearchParser.CATEGORY in item and item[SearchParser.CATEGORY]:
                sri.category = item[SearchParser.CATEGORY]
            if SearchParser.STATE in item and item[SearchParser.STATE]:
                sri.state = item[SearchParser.STATE]
            if SearchParser.SINAGIRE in item and item[SearchParser.SINAGIRE]:
                sri.sinagire = item[SearchParser.SINAGIRE]
            if SearchParser.IMAGE_ON_ERR in item and item[SearchParser.IMAGE_ON_ERR]:
                sri.img_on_err = item[SearchParser.IMAGE_ON_ERR]
            
            results.append(sri)
        return results

    
    @classmethod
    def convertMakepureItem(cls, item :Dict) -> MakepureItem:
        mkpr = MakepureItem()
        if SearchParser.TITLE in item:
            mkpr.title = item[SearchParser.TITLE]
        if SearchParser.MAKEPURE_BIKO in item:
            mkpr.biko = item[SearchParser.MAKEPURE_BIKO]
        if SearchParser.MAKEPURE_URL in item:
            mkpr.url = item[SearchParser.MAKEPURE_URL]
        stptn = r'(マケプレ)(￥[0-9,]*)'
        val = item[SearchParser.MAKEPURE]
        m = re.findall(stptn, val)
        if len(m) != 0:
             mkpr.price = str(m[0][1])
        return mkpr

    @classmethod
    def convertMainItem(cls, item :Dict) -> Optional[MainItem]:
        maini = MainItem()
        if SearchParser.TITLE in item:
            maini.title = item[SearchParser.TITLE]
        if SearchParser.TITLE_URL in item:
            maini.url = item[SearchParser.TITLE_URL]
        if SearchParser.PRICE in item:
            maini.used = ItemPrice(price=item[SearchParser.PRICE])
        if SearchParser.USED in item:
            stptn = r'(中古(価格)?：)?(￥?[0-9,]*円?).*?(（?税込）?)?'
            val = item[SearchParser.USED]
            m = re.findall(stptn, val)
            if len(m) != 0: 
                ip = ItemPrice(price=str(m[0][2]),
                               price_pre_text=str(m[0][0]),
                               price_tail_text=str(m[0][3]),
                               )
                maini.used = ip
        if SearchParser.NEW in item:
            stptn = r'(新品(価格)?：)?(￥?[0-9,]*円?).*?(（?税込）?)?'
            val = item[SearchParser.NEW]
            m = re.findall(stptn, val)
            if len(m) != 0: 
                ip = ItemPrice(price=str(m[0][2]),
                               price_pre_text=str(m[0][0]),
                               price_tail_text=str(m[0][3]),
                               )
                maini.new = ip

        if maini.new or maini.used:
            return maini
        return None
    
    @classmethod
    def createURLParamForTemplateValue(cls, urlparam :Dict, pageinfo :Dict) -> str:
        current_page_num = FilterDefault.PAGE
        if SearchCmn.CURRENT in pageinfo:
            current_page_num = int(pageinfo[SearchCmn.CURRENT])
        return cls.createURLParam(urlparam, current_page_num)
    