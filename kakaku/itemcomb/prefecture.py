from accessor.read_sqlalchemy import Session
from accessor.store import PrefectureQuery
from model.store import Prefecture
from common import const_value


class PrefectureName:
    PREF_ALL = [
        "北海道",
        "青森県",
        "岩手県",
        "宮城県",
        "秋田県",
        "山形県",
        "福島県",
        "茨城県",
        "栃木県",
        "群馬県",
        "埼玉県",
        "千葉県",
        "東京都",
        "神奈川県",
        "新潟県",
        "富山県",
        "石川県",
        "福井県",
        "山梨県",
        "長野県",
        "岐阜県",
        "静岡県",
        "愛知県",
        "三重県",
        "滋賀県",
        "京都府",
        "大阪府",
        "兵庫県",
        "奈良県",
        "和歌山県",
        "鳥取県",
        "島根県",
        "岡山県",
        "広島県",
        "山口県",
        "徳島県",
        "香川県",
        "愛媛県",
        "高知県",
        "福岡県",
        "佐賀県",
        "長崎県",
        "熊本県",
        "大分県",
        "宮崎県",
        "鹿児島県",
        "沖縄県",
    ]
    COUNTRYWIDE_PREF_NAME = "共通"

    def __init__(self) -> None:
        pass

    @classmethod
    def get_all_prefecturename(cls):
        return cls.PREF_ALL.copy()

    @classmethod
    def get_country_wide_name(cls):
        return cls.COUNTRYWIDE_PREF_NAME


class PrefectureDBSetting:
    @classmethod
    def init_setting(cls, db: Session):
        pref_init_list: list[str] = [PrefectureName.get_country_wide_name()]
        pref_init_list.extend(PrefectureName.get_all_prefecturename())
        db_pref_list = PrefectureQuery.get_by_prefname_list(
            db, prefname_list=pref_init_list
        )
        if db_pref_list and len(pref_init_list) == len(db_pref_list):
            return
        if not db_pref_list:
            pref_list: list[Prefecture] = [
                Prefecture(pref_id=id, name=prefname)
                for id, prefname in enumerate(pref_init_list, const_value.NONE_PREF_ID)
            ]
            PrefectureQuery.add_all(db=db, pref_list=pref_list)
            return
        add_list: list[Prefecture] = []
        db_prefname_list = [pref.name for pref in db_pref_list]
        for prefname in pref_init_list:
            if prefname in db_prefname_list:
                continue
            add_list.append(Prefecture(name=prefname))
        PrefectureQuery.add_all(db=db, pref_list=add_list)
