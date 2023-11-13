from accessor import read_sqlalchemy as rsql

print(f"dbconf={rsql.dbconf}")
print(f"url_obj={rsql.url_obj}")
print(f"is_echo={rsql.is_echo}")
eng = rsql.getEngine()

