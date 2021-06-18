from typing import Any

from src.utility.EntityUtility import Entity
from src.utility.StructUtility import Struct
from src.utility.filter.StructFilter import StructFilter


class EntityFilter(StructFilter):

    def all_entities(self, structs: [Struct]) -> [Entity]:
        return filter(lambda x: isinstance(x, Entity), structs)

    def all_empties(self, structs: [Struct]) -> [Entity]:
        return filter(lambda x: isinstance(x, Entity) and x.is_empty(), structs)