from typing import List

from blenderproc.python.types.MeshObjectUtility import MeshObject


def light_surface(objects: List[MeshObject], emission_strength: float = 10.0,
                  keep_using_base_color: bool = False, emission_color: list = None):
    """ Add emission shader to the materials of the given objects.

    :param objects: A list of mesh objects whose materials should emit light.
    :param emission_strength: The strength of the emitted light.
    :param keep_using_base_color: If True, the base color of the material will be used as emission color.
    :param emission_color: The color of the light to emit. Is ignored if keep_using_base_color is set to True.
    """
    empty_material = None

    # for each object add a material
    for obj in objects:
        if not obj.has_materials():
            # If this is the first object without any material
            if empty_material is None:
                # this object has no material so far -> create one
                empty_material = obj.new_material("TextureLess")
            else:
                # Just reuse the material that was already created for other objects with no material
                obj.add_material(empty_material)
                # Material has already been made emissive, so go to the next object
                continue

        for i, material in enumerate(obj.get_materials()):
            if material is None:
                continue
            # if there is more than one user make a copy and then use the new one
            if material.get_users() > 1:
                material = material.duplicate()
                obj.set_material(i, material)
            # rename the material
            material.set_name(material.get_name() + "_emission")
            # add a custom property to later identify these materials
            material.set_cp("is_lamp", True)

            material.make_emissive(emission_strength=emission_strength, emission_color=emission_color,
                                   keep_using_base_color=keep_using_base_color)




