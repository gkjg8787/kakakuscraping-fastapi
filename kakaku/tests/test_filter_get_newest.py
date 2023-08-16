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

