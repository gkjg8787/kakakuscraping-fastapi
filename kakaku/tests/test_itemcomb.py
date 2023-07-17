
from itemcomb.storepostage import getAndRegistShippingTermsByItemId
def test_get_storepostage():
    item_id_list = [1,2]
    ret = getAndRegistShippingTermsByItemId(item_id_list)
    print(ret)
    assert len(ret) != 0

def test_parse_boundary_of_Terms():
    from template_value.calcitemcomb import Terms
    from common.templates_string import HTMLOption
    t = Terms(terms_index=1,
          boundary="1500>:1000<=",
          postage="440",
          created_at="2023-01-01 00:00:00")
    assert t.boundary1 == "1500"
    assert t.ope[0].lt == HTMLOption.SELECTED.value
    assert t.boundary2 == "1000"
    assert t.ope[1].ge == HTMLOption.SELECTED.value