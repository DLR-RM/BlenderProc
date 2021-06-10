# ----------------
# V-HACD Blender add-on
# Copyright (c) 2014, Alain Ducharme
# ----------------
# This software is provided 'as-is', without any express or implied warranty.
# In no event will the authors be held liable for any damages arising from the use of this software.
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it freely,
# subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

#
# NOTE: requires/calls Khaled Mamou's VHACD executable found here: https://github.com/kmammou/v-hacd/
# We specifically asked for the permission to use this inside BlenderProc. All rights are still with Khaled Mamou.

import os
from sys import platform

import git

from src.utility.Utility import Utility
import bpy
from mathutils import Matrix
import bmesh
from subprocess import Popen
import shutil

def convex_decomposition(ob, temp_dir, resolution=1000000, name_template="?_hull_#", remove_doubles=True, apply_modifiers=True, apply_transforms="NONE", depth=20, concavity=0.0025, plane_downsampling=4, convexhull_downsampling=4, alpha=0.05, beta=0.05, gamma=0.00125, pca=False, mode="VOXEL", max_num_vertices_per_ch=32, min_volume_per_ch=0.0001, cache_dir=None):
    """ Uses V-HACD to decompose the given object.

    :param ob: The blender object to decompose.
    :param temp_dir: The temp directory where to store the convex parts.
    :param resolution: maximum number of voxels generated during the voxelization stage
    :param name_template: The template how to name the convex parts.
    :param remove_doubles: Remove double vertices before decomposition.
    :param apply_modifiers: Apply modifiers before decomposition.
    :param apply_transforms: Apply transforms before decomposition.
    :param depth: maximum number of clipping stages. During each split stage, all the model parts (with a concavity higher than the user defined threshold) are clipped according the "best" clipping plane
    :param concavity: maximum concavity
    :param plane_downsampling: controls the granularity of the search for the "best" clipping plane
    :param convexhull_downsampling: controls the precision of the convex-hull generation process during the clipping plane selection stage
    :param alpha: controls the bias toward clipping along symmetry planes
    :param beta: controls the bias toward clipping along revolution axes
    :param gamma: maximum allowed concavity during the merge stage
    :param pca: enable/disable normalizing the mesh before applying the convex decomposition
    :param mode: 0: voxel-based approximate convex decomposition, 1: tetrahedron-based approximate convex decomposition
    :param max_num_vertices_per_ch: controls the maximum number of triangles per convex-hull
    :param min_volume_per_ch: controls the adaptive sampling of the generated convex-hulls
    :param cache_dir: If a directory is given, convex decompositions are stored there named after the meshes hash. If the same mesh is decomposed a second time, the result is loaded from the cache and the actual decomposition is skipped.
    :return: The list of convex parts composing the given object.
    """
    if platform != "linux" and platform != "linux2":
        raise Exception("Convex decomposition is at the moment only available on linux.")

    # Download v-hacd library if necessary
    vhacd_path = Utility.resolve_path("external/vhacd")
    if not os.path.exists(os.path.join(vhacd_path, "v-hacd")):
        print("Downloading v-hacd library into " + str(vhacd_path))
        git.Git(vhacd_path).clone("git://github.com/kmammou/v-hacd.git")

        print("Building v-hacd")
        os.system(os.path.join(vhacd_path, "build_linux.sh"))

    off_filename = os.path.join(temp_dir, 'vhacd.off')
    outFileName = os.path.join(temp_dir, 'vhacd.wrl')
    logFileName = os.path.join(temp_dir, 'vhacd_log.txt')

    # Apply modifiers
    bpy.ops.object.select_all(action='DESELECT')
    if apply_modifiers:
        mesh = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.copy()
    else:
        mesh = ob.data.copy()

    # Apply transforms
    translation, quaternion, scale = ob.matrix_world.decompose()
    scale_matrix = Matrix(((scale.x, 0, 0, 0), (0, scale.y, 0, 0), (0, 0, scale.z, 0), (0, 0, 0, 1)))
    if apply_transforms in ['S', 'RS', 'LRS']:
        pre_matrix = scale_matrix
        post_matrix = Matrix()
    else:
        pre_matrix = Matrix()
        post_matrix = scale_matrix
    if apply_transforms in ['RS', 'LRS']:
        pre_matrix = quaternion.to_matrix().to_4x4() @ pre_matrix
    else:
        post_matrix = quaternion.to_matrix().to_4x4() @ post_matrix
    if apply_transforms == 'LRS':
        pre_matrix = Matrix.Translation(translation) @ pre_matrix
    else:
        post_matrix = Matrix.Translation(translation) @ post_matrix

    mesh.transform(pre_matrix)

    # Create bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if remove_doubles:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    # Build a hash for the given mesh
    mesh_hash = 0
    for vert in mesh.vertices:
        # Combine the hashes of the local coordinates of all vertices
        mesh_hash = hash((mesh_hash, hash(vert.co[:])))

    if cache_dir is None or not os.path.exists(os.path.join(cache_dir, str(mesh_hash) + ".wrl")):
        vhacd_binary = os.path.join(vhacd_path, "v-hacd", 'bin', "test", "testVHACD")

        # Run V-HACD
        print('\nExporting mesh for V-HACD: {}...'.format(off_filename))
        off_export(mesh, off_filename)
        bpy.data.meshes.remove(mesh)
        cmd_line = ('"{}" --input "{}" --resolution {} --depth {} '
                    '--concavity {:g} --planeDownsampling {} --convexhullDownsampling {} '
                    '--alpha {:g} --beta {:g} --gamma {:g} --pca {:b} --mode {:b} '
                    '--maxNumVerticesPerCH {} --minVolumePerCH {:g} --output "{}" --log "{}"').format(
            vhacd_binary, off_filename, resolution, depth,
            concavity, plane_downsampling, convexhull_downsampling,
            alpha, beta, gamma, pca, mode == 'TETRAHEDRON',
            max_num_vertices_per_ch, min_volume_per_ch, outFileName, logFileName)

        print('Running V-HACD...\n{}\n'.format(cmd_line))
        vhacd_process = Popen(cmd_line, bufsize=-1, close_fds=True, shell=True)
        vhacd_process.wait()

        # Import convex parts
        if not os.path.exists(outFileName):
            raise Exception("No output produced by convex decomposition of object " + ob.name)

        if cache_dir is not None:
            # Create cache dir, if it not exists yet
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            # Copy decomposition into cache dir
            shutil.copyfile(outFileName, os.path.join(cache_dir, str(mesh_hash) + ".wrl"))
    else:
        outFileName = os.path.join(cache_dir, str(mesh_hash) + ".wrl")

    bpy.ops.import_scene.x3d(filepath=outFileName, axis_forward='Y', axis_up='Z')
    imported = bpy.context.selected_objects

    # Name and transform the loaded parts
    for index, hull in enumerate(imported):
        hull.select_set(False)
        hull.matrix_basis = post_matrix
        name = name_template.replace('?', ob.name, 1)
        name = name.replace('#', str(index + 1), 1)
        if name == name_template:
            name += str(index + 1)
        hull.name = name
        hull.data.name = name
        hull.display_type = 'WIRE'

    return imported

def off_export(mesh, fullpath):
    """ Export triangulated mesh to Object File Format """
    with open(fullpath, 'wb') as off:
        off.write(b'OFF\n')
        off.write(str.encode('{} {} 0\n'.format(len(mesh.vertices), len(mesh.polygons))))
        for vert in mesh.vertices:
            off.write(str.encode('{:g} {:g} {:g}\n'.format(*vert.co)))
        for face in mesh.polygons:
            off.write(str.encode('3 {} {} {}\n'.format(*face.vertices)))
