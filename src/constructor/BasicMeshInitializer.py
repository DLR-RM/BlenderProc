import bpy

from src.main.Module import Module
from src.utility.Config import Config


class BasicMeshInitializer(Module):
    """ Adds/initializes basic mesh objects in the scene. Allows setting the basic attribute values. For more precise
        and powerful mesh manipulation use manipulators.EntityManipulator module.
        Can enable default 'Principled BSDF' shader-based material for each of those meshes.

        Example 1: add a Plane mesh "Ground_plane" to the scene.

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

        Example 2: add a rotated "Cube_1" Cube mesh, a displaced "Torus_2" Torus mesh, and a scaled "Cone_3" objects to
                   the scene.

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

    .. csv-table::
       :header: "Keyword", "Description"

       "meshes_to_add", "List that contains a mesh configuration data in each cell. See table below for available "
                        "parameters per cell. Type: list."
       "init_materials", "Flag that controls whether the added (if True) meshes will be assigned a default Principled "
                         "BSDF shader-based material, or not (if False). Material name is derived from the object name "
                         "(plus a "_material" suffix). Optional. Default value: True. Type: boolean."

    **meshes_to_add cell configuration**:

    .. csv-table::
       :header: "Keyword", "Description"

       "type", "Type of mesh object to add. Available types: 'plane', 'cube', 'circle', 'uvsphere', 'icosphere', "
               "'cylinder', 'cone', 'torus'. Type: string."
       "name", "Name of the mesh object. Type: string."
       "location", "Location of the mesh object. Optional. Default value: [0, 0, 0]. Type: mathutils.Vector."
       "rotation", "Rotation (3 Euler angles) of the mesh object. Optional. Default value: [0, 0, 0]. "
                   "Type: mathutils.Vector."
       "scale", "Scale of the mesh object. Optional. Default value: [1, 1, 1]. Type: mathutils.Vector."
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Adds specified basic meshes to the scene and sets at least their names to the user-defined ones. """
        meshes_to_add = self.config.get_list("meshes_to_add")
        init_meshes_mats = self.config.get_bool("init_materials", True)
        for mesh in meshes_to_add:
            mesh_conf = Config(mesh)
            mesh_type = mesh_conf.get_string("type")
            mesh_name = mesh_conf.get_string("name")
            mesh_location = mesh_conf.get_vector3d("location", [0, 0, 0])
            mesh_rotation = mesh_conf.get_vector3d("rotation", [0, 0, 0])
            mesh_scale = mesh_conf.get_vector3d("scale", [1, 1, 1])
            self._add_mesh(mesh_type)
            self._set_attrs(mesh_name, mesh_location, mesh_rotation, mesh_scale)
            if init_meshes_mats:
                self._init_material(mesh_name)

    def _add_mesh(self, mesh_type):
        """ Adds a mesh to the scene.

        :param mesh_type: Type of the mesh to add. Type: string.
        """
        if mesh_type == "plane":
            bpy.ops.mesh.primitive_plane_add()
        elif mesh_type == "cube":
            bpy.ops.mesh.primitive_cube_add()
        elif mesh_type == "circle":
            bpy.ops.mesh.primitive_circle_add()
        elif mesh_type == "uvsphere":
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif mesh_type == "icosphere":
            bpy.ops.mesh.primitive_ico_sphere_add()
        elif mesh_type == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add()
        elif mesh_type == "cone":
            bpy.ops.mesh.primitive_cone_add()
        elif mesh_type == "torus":
            bpy.ops.mesh.primitive_torus_add()
        else:
            raise RuntimeError('Unknown basic mesh type "{}"! Available types: "plane", "cube", "circle", "uvsphere", '
                               '"icosphere", "cylinder", "cone", "torus".'.format(type))

    def _set_attrs(self, mesh_name, mesh_location, mesh_rotation, mesh_scale):
        """ Sets the attribute values of the added mesh.

        :param mesh_name: Name of the mesh. Type: string.
        :param mesh_location: XYZ location of the mesh. Type: mathutils.Vector.
        :param mesh_rotation: Rotation (3 Euler angles) of the mesh. Type: mathutils.Vector.
        :param mesh_scale: Scale of the mesh. Type: mathutils.Vector.
        """
        bpy.context.object.name = mesh_name
        bpy.context.object.location = mesh_location
        bpy.context.object.rotation_euler = mesh_rotation
        bpy.context.object.scale = mesh_scale

    def _init_material(self, mesh_name):
        """ Adds a new default material and assigns it to the added mesh object. """
        mat_obj = bpy.data.materials.new(name=mesh_name+"_material")
        mat_obj.use_nodes = True
        bpy.context.object.data.materials.append(mat_obj)
