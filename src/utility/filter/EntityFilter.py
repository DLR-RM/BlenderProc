from typing import Any

from src.utility.EntityUtility import Entity
from src.utility.StructUtility import Struct
from src.utility.filter.StructFilter import StructFilter


class EntityFilter(StructFilter):

    @staticmethod
    def all_entities(structs: [Struct]) -> [Entity]:
        """ Returns all entities from the given list.

        :param structs: A list of elements.
        :return: All entities from the given list.
        """
        return filter(lambda x: isinstance(x, Entity), structs)

    @staticmethod
    def all_empties(structs: [Struct]) -> [Entity]:
        """ Returns all empty entities from the given list.

        :param structs: A list of elements.
        :return: All entities with type "EMPTY" from the given list.
        """
        return filter(lambda x: isinstance(x, Entity) and x.is_empty(), structs)