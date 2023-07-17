from accessor.item import (
    ItemQuery,
    NewestQuery,
    UrlQuery,
)
from accessor.item.item import OrganizerQuery

def test_get_most_recent_old_price_by_url_id():
    url_id = 7
    val = ItemQuery.get_most_recent_old_price_by_url_id(url_id=url_id)
    assert int(val) == 2700

def test_get_most_recent_old_price_by_item_id():
    item_id = 7
    val = ItemQuery.get_most_recent_old_price_by_item_id(item_id=item_id)
    assert int(val) == 2211

def test_get_lowest_price_ever():
    item_id = 7
    val = NewestQuery.get_lowest_price_ever(item_id=item_id)
    assert int(val) == 2211

def test_organizerquery_get_pricelog_2days_today():
    val = OrganizerQuery.get_pricelog_2days_today()
    assert len(val) == 0

def test_organizerquery_get_pricelog_today():
    val = OrganizerQuery.get_pricelog_today()
    assert len(val) == 0