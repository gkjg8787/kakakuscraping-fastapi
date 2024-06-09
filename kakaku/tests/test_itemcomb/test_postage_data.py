from itemcomb import postage_data as posd


def assert_get_list_of_boundary_value_and_operation(
    boundary_text: str, result: list[dict]
):
    div_list = posd.ShippingTermsBoundary.get_list_of_boundary_value_and_operation(
        boundary_text
    )
    assert len(div_list) == len(result)
    for div, res in zip(div_list, result):
        assert div["boundary_ope"] == res["boundary_ope"]
        assert div["boundary_val"] == res["boundary_val"]


def test_postage_data_shipping_terms_boundary_get_list_of_boundary_value_and_operation_success_1():
    testdata = {"boundary": "0<", "result": [{"boundary_val": 0, "boundary_ope": "<"}]}
    assert_get_list_of_boundary_value_and_operation(
        testdata["boundary"], testdata["result"]
    )


def test_postage_data_shipping_terms_boundary_get_list_of_boundary_value_and_operation_success_2():
    testdata = {
        "boundary": "0<=:2000>",
        "result": [
            {"boundary_val": 0, "boundary_ope": "<="},
            {"boundary_val": 2000, "boundary_ope": ">"},
        ],
    }
    assert_get_list_of_boundary_value_and_operation(
        testdata["boundary"], testdata["result"]
    )


def test_postage_data_shipping_terms_boundary_get_list_of_boundary_value_and_operation_success_3():
    testdata = {
        "boundary": "300<:1500>=",
        "result": [
            {"boundary_val": 300, "boundary_ope": "<"},
            {"boundary_val": 1500, "boundary_ope": ">="},
        ],
    }
    assert_get_list_of_boundary_value_and_operation(
        testdata["boundary"], testdata["result"]
    )


def assert_add_terms_to_boundary(based: dict, addd: dict):
    base_boundary = posd.ShippingTermsBoundary.create_boundary_of_db(
        lower_ope=based["ope"], lower_val=based["val"]
    )
    assert based["result"] == base_boundary
    result = posd.ShippingTermsBoundary.add_terms_to_boundary(
        base_boundary, add_ope=addd["ope"], add_val=addd["val"]
    )
    assert addd["result"] == result


def test_postage_data_shipping_terms_boundary_add_terms_boundary_success_1():
    testdata = {
        "base": {"ope": "<", "val": 500, "result": "500<"},
        "add": {"ope": ">=", "val": 2000, "result": "500<:2000>="},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_success_2():
    testdata = {
        "base": {"ope": ">", "val": 2000, "result": "2000>"},
        "add": {"ope": "<=", "val": 700, "result": "700<=:2000>"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_success_3():
    testdata = {
        "base": {"ope": "<=", "val": 0, "result": "0<="},
        "add": {"ope": ">=", "val": 1000, "result": "0<=:1000>="},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_ng_1():
    testdata = {
        "base": {"ope": ">", "val": 1000, "result": "1000>"},
        "add": {"ope": "<", "val": 1200, "result": "1000>"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_ng_2():
    testdata = {
        "base": {"ope": ">", "val": 1000, "result": "1000>"},
        "add": {"ope": ">", "val": 500, "result": "500>"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])


def test_postage_data_shipping_terms_boundary_add_terms_boundary_ng_3():
    testdata = {
        "base": {"ope": "<", "val": 1800, "result": "1800<"},
        "add": {"ope": "<=", "val": 1500, "result": "1800<"},
    }
    assert_add_terms_to_boundary(testdata["base"], testdata["add"])
