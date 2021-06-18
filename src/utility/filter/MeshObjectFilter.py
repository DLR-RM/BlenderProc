from typing import Any

from src.utility.MeshObjectUtility import MeshObject
from src.utility.StructUtility import Struct
from src.utility.filter.StructFilter import StructFilter


class MeshObjectFilter(StructFilter):

    @staticmethod
    def all_mesh_objects(elements: [Struct]) -> [MeshObject]:
        """ Returns all mesh objects from the given list.

        :param elements: A list of elements.
        :return: All mesh objects from the given list.
        """
        return list(filter(lambda x: isinstance(x, MeshObject), elements))

    @staticmethod
    def by_attr(elements: [Struct], attr_name: str, value: Any, regex: bool = False) -> [MeshObject]:
        """ Returns all mesh objects from the given list whose specified attribute has the given value.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param value: The value the attribute should have.
        :param regex: If True, string values will be matched via regex.
        :return: The mesh objects from the given list that match the given value at the specified attribute.
        """
        return StructFilter.by_attr(MeshObjectFilter.all_mesh_objects(elements), attr_name, value, regex)

    @staticmethod
    def one_by_attr(elements: [Struct], attr_name: str, value: Any, regex: bool = False) -> MeshObject:
        """ Returns the one mesh object from the given list whose specified attribute has the given value.

        An error is thrown is more than one or no element has been found.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param value: The value the attribute should have.
        :param regex: If True, string values will be matched via regex.
        :return: The one mesh object from the given list that matches the given value at the specified attribute.
        """
        return StructFilter.one_by_attr(MeshObjectFilter.all_mesh_objects(elements), attr_name, value, regex)

    @staticmethod
    def by_cp(elements: [Struct], cp_name: str, value: Any, regex: bool = False) -> [MeshObject]:
        """  Returns all mesh objects from the given list whose specified custom property has the given value.

        :param elements: A list of elements.
        :param cp_name: The name of the custom property to look for.
        :param value: The value the custom property should have.
        :param regex: If True, string values will be matched via regex.
        :return: The mesh objects from the given list that match the given value at the specified custom property.
        """
        return StructFilter.by_cp(MeshObjectFilter.all_mesh_objects(elements), cp_name, value, regex)

    @staticmethod
    def one_by_cp(elements: [Struct], cp_name: str, value: Any, regex: bool = False) -> MeshObject:
        """ Returns the one mesh object from the given list whose specified custom property has the given value.

        An error is thrown is more than one or no element has been found.

        :param elements: A list of elements.
        :param cp_name: The name of the custom property to look for.
        :param value: The value the custom property should have.
        :param regex: If True, string values will be matched via regex.
        :return: The one mesh object from the given list that matches the given value at the specified custom property.
        """
        return StructFilter.one_by_cp(MeshObjectFilter.all_mesh_objects(elements), cp_name, value, regex)

    @staticmethod
    def by_attr_in_interval(elements: [Struct], attr_name: str, min_value: Any = None, max_value: Any = None) -> [Struct]:
        """ Returns all mesh objects from the given list whose specified attribute has a value in the given interval.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param min_value: The minimum value of the interval.
        :param max_value: The maximum value of the interval.
        :return: The mesh objects from the given list that match the given value at the specified attribute.
        """
        return StructFilter.by_attr_in_interval(MeshObjectFilter.all_mesh_objects(elements), attr_name, min_value, max_value)

    @staticmethod
    def by_attr_outside_interval(elements: [Struct], attr_name: str, min_value: Any = None, max_value: Any = None) -> [Struct]:
        """ Returns all mesh objects from the given list whose specified attribute has a value outside the given interval.

        :param elements: A list of elements.
        :param attr_name: The name of the attribute to look for.
        :param min_value: The minimum value of the interval.
        :param max_value: The maximum value of the interval.
        :return: The mesh objects from the given list that match the given value at the specified attribute.
        """
        return StructFilter.by_attr_outside_interval(MeshObjectFilter.all_mesh_objects(elements), attr_name, min_value, max_value)