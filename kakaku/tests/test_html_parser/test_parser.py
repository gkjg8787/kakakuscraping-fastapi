from html_parser import htmlparse

def test_parseiteminfo_get_trendrate():
    pi = htmlparse.ParseItemInfo()
    pi.oldPrice = 600
    pi.usedPrice = 670
    assert round(pi.getTrendRate(),5) == 0.11667