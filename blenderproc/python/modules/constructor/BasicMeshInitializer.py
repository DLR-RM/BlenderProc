import bpy

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config


class BasicMeshInitializer(Module):
    """
    Adds/initializes basic mesh objects in the scene. Allows setting the basic attribute values. Can initialize a
    default 'Principled BSDF' shader-based material for each of added objects. For more precise and powerful object
    manipulation use manipulators.EntityManipulator module.

    Example 1: Add a plane "Ground_plane" object to the scene.

    .. code-block:: yaml

        {
          "module": "constructor.BasicMeshInitializer",
          "config": {
            "meshes_to_add": [
            {
              "type": "plane",
              "name": "Ground_plane"
            }
            ]
          }
        }

    Example 2: Add a rotated "Cube_1" cube object, a displaced "Torus_2" torus object, and a scaled "Cone_3" cone
    object to the scene.

    .. code-block:: yaml

        {
          "module": "constructor.BasicMeshInitializer",
          "config": {
            "meshes_to_add": [
            {
              "type": "cube",
              "name": "Cube_1",
              "rotation": [1.1, 0.2, 0.2]
            },
            {
              "type": "torus",
              "name": "Torus_2",
              "location": [0, 0, 3]
            },
            {
              "type": "cone",
              "name": "Cone_3",
              "scale": [2, 3, 4]
            }
            ]
          }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - meshes_to_add
          - List that contains object configuration data in each cell. See table below for available parameters per
            cell. 
          - list
        * - init_materials
          - Flag that controls whether the added objects will be assigned a default Principled BSDF shader-based
            material (if value is True), or not (if value is False). Material's name is derived from the object's
            name. Default: True.
          - boolean

    **meshes_to_add cell configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - type
          - Type of mesh object to add. Available types: 'plane', 'cube', 'circle', 'uvsphere', 'icosphere',
            'cylinder', 'cone', 'torus'. 
          - string
        * - name
          - Name of the mesh object.
          - string
        * - location
          - Location of the mesh object. Default: [0, 0, 0].
          - mathutils.Vector
        * - rotation
          - Rotation (3 Euler angles) of the mesh object. Default: [0, 0, 0].
          - mathutils.Vector
        * - scale
          - Scale of the mesh object. Default: [1, 1, 1].
          - mathutils.Vector
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Adds specified basic mesh objects to the scene and sets at least their names to the user-defined ones.
            1. Get configuration parameters' values.
            2. Add an object.
            3. Set attribute values.
            4. Initialize a material, if needed.
        """
        meshes_to_add = self.config.get_list("meshes_to_add")
        init_objs_mats = self.config.get_bool("init_materials", True)
        for mesh in meshes_to_add:
            mesh_conf = Config(mesh)
            obj_type = mesh_conf.get_string("type")
            obj_name = mesh_conf.get_string("name")
            obj_location = mesh_conf.get_vector3d("location", [0, 0, 0])
            obj_rotation = mesh_conf.get_vector3d("rotation", [0, 0, 0])
            obj_scale = mesh_conf.get_vector3d("scale", [1, 1, 1])
            new_obj = self._add_obj(obj_type)
            self._set_attrs(new_obj, obj_name, obj_location, obj_rotation, obj_scale)
            if init_objs_mats:
                self._init_material(obj_name)

    def _add_obj(self, obj_type):
        """ Adds an object to the scene.

        :param obj_type: Type of the object to add. Type: string.
        :return: Added object. Type: bpy.types.Object.
        """
        if obj_type == "plane":
            bpy.ops.mesh.primitive_plane_add()
        elif obj_type == "cube":
            bpy.ops.mesh.primitive_cube_add()
        elif obj_type == "circle":
            bpy.ops.mesh.primitive_circle_add()
        elif obj_type == "uvsphere":
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif obj_type == "icosphere":
            bpy.ops.mesh.primitive_ico_sphere_add()
        elif obj_type == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add()
        elif obj_type == "cone":
            bpy.ops.mesh.primitive_cone_add()
        elif obj_type == "torus":
            bpy.ops.mesh.primitive_torus_add()
        else:
            raise RuntimeError('Unknown basic mesh type "{}"! Available types: "plane", "cube", "circle", "uvsphere", '
                               '"icosphere", "cylinder", "cone", "torus".'.format(type))

        new_obj = bpy.context.object

        return new_obj

    def _set_attrs(self, new_obj, obj_name, obj_location, obj_rotation, obj_scale):
        """ Sets the attribute values of the added object.

        :param new_obj: New object to modify. Type: bpy.types.Object.
        :param obj_name: Name of the object. Type: string.
        :param obj_location: XYZ location of the object. Type: mathutils.Vector.
        :param obj_rotation: Rotation (3 Euler angles) of the object. Type: mathutils.Vector.
        :param obj_scale: Scale of the object. Type: mathutils.Vector.
        """
        new_obj.name = obj_name
        new_obj.location = obj_location
        new_obj.rotation_euler = obj_rotation
        new_obj.scale = obj_scale

    def _init_material(self, obj_name):
        """ Adds a new default material and assigns it to the added mesh object.

        :param obj_name: Name of the object. Type: string.
        """
        mat_obj = bpy.data.materials.new(name=obj_name+"_material")
        mat_obj.use_nodes = True
        bpy.context.object.data.materials.append(mat_obj)
