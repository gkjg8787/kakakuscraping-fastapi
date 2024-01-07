import re
from enum import Enum, auto



class InsertProcType(Enum):
    ITEM_UPDATE = auto()
    MAKEPURE_TOOL = auto()
    SURUGAYA_MAILORDER_FEE = auto()
    NETOFF_SHIPPING_SURCHARGE = auto()
    BOOKOFF_SHIPPING_TERMS = auto()
    GEO_SHIPPING_TERMS = auto()

class BoundaryOperator(Enum):
    GT = ("gt", "<", "より大きい")
    GE = ("ge", "<=", "以上")
    LT = ("lt", ">", "より小さい")
    LE = ("le", ">=", "以下")

    def __init__(self, lower_name :str, operator_str :str, jtext :str):
        self.lower = lower_name
        self.operator = operator_str
        self.jtext = jtext
    
    @classmethod
    def get(cls, lower :str = "", operator :str = "", jtext :str = ""):
        if lower:
            for c in cls:
                if c.lower == lower:
                    return c
        if operator:
            for c in cls:
                if c.operator == operator:
                    return c
        if jtext:
            for c in cls:
                if c.jtext == jtext:
                    return c
        return None
    
    
class ShippingTermsBoundary:
    boundary_operation_list = ["<=", ">=", "<", ">"]
    
    @classmethod
    def get_list_of_boundary_value_and_operation(cls, boundary_text :str):
        results :list[dict] = []
        def get_boundary_and_ope(btext :str):
            m = re.findall(r"([1-9][0-9]+|0)(>=|<=|>|<)", btext)
            if not m:
                return {}
            return {"boundary_val":int(m[0][0]), "boundary_ope":str(m[0][1])}
        if ":" in boundary_text:
            for b in boundary_text.split(":"):
                ret = get_boundary_and_ope(b)
                if not ret:
                    continue
                results.append(ret)
        else:
            ret = get_boundary_and_ope(boundary_text)
            if ret:
                results.append(ret)
        return results
    
    @classmethod
    def reverse_operator(cls, boundary_ope :str):
        match boundary_ope:
            case "<=":
                return ">"
            case "<":
                return ">="
            case ">=":
                return "<"
            case ">":
                return "<="
            case _:
                raise ValueError("unsupported boundary operation")
    
    @classmethod
    def create_boundary_of_db(cls,
                              lower_ope :str,
                              lower_val :int,
                              upper_ope :str | None = None,
                              upper_val :int | None = None
                              ):
        if not lower_ope in cls.boundary_operation_list:
            raise ValueError("unsupported boundary operation")
        lower_boundary = f"{lower_val}{lower_ope}"
        if upper_ope is None or upper_val is None:
            return lower_boundary
        return f"{lower_boundary}:{upper_val}{upper_ope}"
    
    @classmethod
    def add_terms_to_boundary(cls,
                              boundary :str,
                              add_ope :str,
                              add_val :int
                              ):
        b_list :list = cls.get_list_of_boundary_value_and_operation(boundary)
        if not b_list:
            return cls.create_boundary_of_db(lower_ope=add_ope, lower_val=add_val)
        if len(b_list) > 1:
            return boundary
        if int(b_list[0]["boundary_val"]) <= add_val:
            lower_val = int(b_list[0]["boundary_val"])
            lower_ope = b_list[0]["boundary_ope"]
            upper_val = add_val
            upper_ope = add_ope
        else:
            lower_val = add_val
            lower_ope = add_ope
            upper_val = int(b_list[0]["boundary_val"])
            upper_ope = b_list[0]["boundary_ope"]
        if lower_ope == upper_ope:
            if lower_ope == ">" or lower_ope == ">=":
                return cls.create_boundary_of_db(lower_ope=lower_ope, lower_val=lower_val)
            if lower_ope == "<" or lower_ope == "<=":
                return cls.create_boundary_of_db(lower_ope=upper_ope, lower_val=upper_val)
        def check_operator_discrepancies(lower_ope :str, upper_ope :str):
            if lower_ope == ">=" or lower_ope == ">":
                return False
            if upper_ope == "<=" or upper_ope == "<":
                return False
            return True
        if not check_operator_discrepancies(lower_ope=lower_ope, upper_ope=upper_ope):
            return boundary
        return cls.create_boundary_of_db(lower_ope=lower_ope,
                                         lower_val=lower_val,
                                         upper_ope=upper_ope,
                                         upper_val=upper_val
                                         )
        
    