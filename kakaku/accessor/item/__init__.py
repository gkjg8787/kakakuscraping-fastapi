from typing import List
from sqlalchemy import (
    select,
    insert,
    delete,
    update,
    tuple_,
    union,
)
from sqlalchemy.orm import Session

from datetime import datetime

from model import item
from accessor.read_sqlalchemy import getEngine

from .item import (
    NewestQuery,
    GroupQuery,
    ItemQuery,
    UrlQuery,
    UrlActive,
)
#from .raw_item import NewestQuery
#from .lite_item import NewestQuery