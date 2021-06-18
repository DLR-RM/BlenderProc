from typing import Any

from src.utility.StructUtility import Struct
import mathutils
import re

class StructFilter:
    @staticmethod
    def check_its_one(structs: [Struct]) -> Struct:
        if len(structs) != 1:
            raise Exception("")
        return structs[0]

    @staticmethod
    def check_equality(attr_value, filter_value, regex):
        if isinstance(attr_value, mathutils.Vector):
            filter_value = mathutils.Vector(filter_value)
        elif isinstance(attr_value, mathutils.Euler):
            filter_value = mathutils.Euler(filter_value)
        elif isinstance(attr_value, mathutils.Color):
            filter_value = mathutils.Color(filter_value)

        if isinstance(attr_value, str) and regex:
            return re.fullmatch(filter_value, attr_value)
        else:
            return filter_value == attr_value

    @staticmethod
    def by_attr(structs: [Struct], attr_name: str, value: Any, regex: bool = False) -> [Struct]:
        return filter(lambda struct: StructFilter.check_equality(struct.get_attr(attr_name), value, regex), structs)

    @staticmethod
    def one_by_attr(structs: [Struct], attr_name: str, value: Any, regex: bool = False) -> Struct:
        structs = StructFilter.by_attr(structs, attr_name, value, regex)
        return StructFilter.check_its_one(structs)

    @staticmethod
    def by_cp(structs: [Struct], cp_name: str, value: Any, regex: bool = False) -> [Struct]:
        return filter(lambda struct: struct.has_cp(cp_name) and StructFilter.check_equality(struct.get_cp(cp_name), value, regex), structs)

    @staticmethod
    def one_by_cp(structs: [Struct], cp_name: str, value: Any, regex: bool = False) -> Struct:
        structs = StructFilter.by_cp(structs, cp_name, value, regex)
        return StructFilter.check_its_one(structs)

    @staticmethod
    def by_attr_in_interval(structs: [Struct], attr_name: str, min_value: Any = None, max_value: Any = None):
        return filter(lambda struct: (min_value is None or min_value < struct.get_attr(attr_name)) and (max_value is None or max_value > struct.get_attr(attr_name)), structs)

    @staticmethod
    def by_attr_outside_interval(structs: [Struct], attr_name: str, min_value: Any = None, max_value: Any = None):
        return filter(lambda struct: (min_value is None or min_value > struct.get_attr(attr_name)) and (max_value is None or max_value < struct.get_attr(attr_name)), structs)
