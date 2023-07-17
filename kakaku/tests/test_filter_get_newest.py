from accessor.item import (
    NewestQuery,
    ItemQuery,
)


from common.filter_name import ActFilterName

def test_sql_get_filter_newest_data():
    filter = {
        "act":ActFilterName.ALL.id
    }
    stmt = NewestQuery.get_newest_filter_statement(filter)
    print(stmt.compile(compile_kwargs={"literal_binds": True}))
    #print(ret)


def test_sql_get_most_recent_old_price():
    print(ItemQuery.get_most_recent_old_price(1))

if __name__ == '__main__':
    #test_sql_get_filter_newest_data()
    test_sql_get_most_recent_old_price()