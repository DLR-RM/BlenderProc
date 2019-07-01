#blender --background --python renderRaytracingImage.py  -- <camfile> <house.obj> <output_dir> [<cam_ids>]
import bpy, sys, os
import mathutils
from math import pi
import csv

started_from_commandline = '--' in sys.argv

if started_from_commandline:
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
    cam_file = argv[0]
    obj_file = argv[1]
    output_dir = argv[2]
    if len(argv) > 3:
        cam_ids = [int(x) for x in argv[3].split(",")]
    else:
        cam_ids = None
else:
    # Just a few testing args in case the skript is started from inside blender
    cam_file = "/home_local/wink_do/suncg/generated/presets/open/19676dd35f3bce853c76d1ef9c059486/outputCamerasFile"
    obj_file = "/home_local/wink_do/suncg/tmp/render/house.obj"
    output_dir = "/home/wink_do/PycharmProjects/LearnedEncoding/render/"
    cam_ids = None

# Read in lights
lights = {}
with open("suncg/light_geometry_compact.txt") as f:
    lines = f.readlines()
    for row in lines:
        row = row.strip().split()
        lights[row[0]] = [[], []]

        index = 1

        number = int(row[index])
        index += 1

        for i in range(number):
            lights[row[0]][0].append(row[index])
            index += 1

        number = int(row[index])
        index += 1

        for i in range(number):
            lights[row[0]][1].append(row[index])
            index += 1

# Read in windows
windows = []
with open('suncg/ModelCategoryMapping.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["coarse_grained_class"] == "window":
            windows.append(row["model_id"])

scene = bpy.data.scenes["Scene"]

scene.cycles.samples = 256
scene.render.tile_x = 256
scene.render.tile_y = 256
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.pixel_aspect_x = (640.0 / 480)
scene.render.resolution_percentage = 100

# Lightning settings to reduce training time
scene.render.engine = 'CYCLES'
scene.render.layers[0].cycles.use_denoising = True
scene.render.use_simplify = True
scene.render.simplify_subdivision_render = 3
scene.cycles.device = "GPU"
scene.cycles.glossy_bounces = 0
scene.cycles.ao_bounces_render = 3
scene.cycles.max_bounces = 3
scene.cycles.min_bounces = 1
scene.cycles.transmission_bounces = 0
scene.cycles.volume_bounces = 0

# Make sure to use the current GPU
prefs = bpy.context.user_preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
print(prefs.compute_device_type, prefs.get_devices())
for group in prefs.get_devices():
    for d in group:
        d.use = True

# Set background color
world = bpy.data.worlds['World']
world.horizon_color[:3] = (0.535, 0.633, 0.608)

# Import obj (the import will convert all materials to cycle nodes
# bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.obj(filepath=obj_file)  # , axis_forward='Y')

# Create the cam
cam = bpy.data.cameras.new("Camera")
cam_ob = bpy.data.objects.new("Camera", cam)
bpy.context.scene.objects.link(cam_ob)
scene.camera = cam_ob

# Make some objects emit lights
for obj in bpy.context.scene.objects:
    if obj.name.startswith("Model#") or ("#" not in obj.name and obj.name.replace(".", "").isdigit()):
        if "#" in obj.name:
            obj_id = obj.name[len("Model#"):]
        else:
            obj_id = obj.name
        if "." in obj.name:
            obj_id = obj_id[:obj_id.find(".")]

        # In the case of the lamp
        if obj_id in lights:
            for m in obj.material_slots:
                mat_name = m.material.name[m.material.name.find("_") + 1:]
                if "." in mat_name:
                    mat_name = mat_name[:mat_name.find(".")]

                if mat_name in lights[obj_id][0] or mat_name in lights[obj_id][1]:
                    nodes = m.material.node_tree.nodes
                    links = m.material.node_tree.links

                    output = nodes.get("Material Output")
                    emission = nodes.get("Emission")
                    if emission is None:
                        diffuse = nodes.get("Diffuse BSDF")
                        if diffuse is not None:
                            mix_node = nodes.new(type='ShaderNodeMixShader')
                            lightPath_node = nodes.new(type='ShaderNodeLightPath')

                            link = next(l for l in links if l.from_socket == diffuse.outputs[0])
                            to_socket = link.to_socket
                            links.remove(link)

                            links.new(lightPath_node.outputs[0], mix_node.inputs[0])
                            links.new(diffuse.outputs[0], mix_node.inputs[2])
                            links.remove(next(l for l in links if l.to_socket == output.inputs[0]))
                            links.new(mix_node.outputs[0], output.inputs[0])

                            emission_node = nodes.new(type='ShaderNodeEmission')
                            emission_node.inputs[0].default_value = m.material.diffuse_color[:] + (1,)

                            if mat_name in lights[obj_id][0]:
                                # If the material corresponds to light bulb
                                emission_node.inputs[1].default_value = 15
                            else:
                                # If the material corresponds to a lampshade
                                emission_node.inputs[1].default_value = 7

                            links.new(emission_node.outputs[0], mix_node.inputs[1])

        # Make the windows emit light
        if obj_id in windows:
            for m in obj.material_slots:
                nodes = m.material.node_tree.nodes
                links = m.material.node_tree.links

                if m.material.translucency > 0:
                    emission = nodes.get("Emission")
                    if emission is None:
                        output = nodes.get("Material Output")
                        if output is not None:
                            print("Creating emission for " + obj_id)

                            link = next(l for l in links if l.to_socket == output.inputs[0])
                            links.remove(link)

                            mix_node = nodes.new(type='ShaderNodeMixShader')
                            emission_node = nodes.new(type='ShaderNodeEmission')
                            transparent_node = nodes.new(type='ShaderNodeBsdfDiffuse')
                            transparent_node.inputs[0].default_value[:3] = (0.285, 0.5, 0.48)
                            lightPath_node = nodes.new(type='ShaderNodeLightPath')

                            links.new(mix_node.outputs[0], output.inputs[0])
                            links.new(lightPath_node.outputs[0], mix_node.inputs[0])
                            links.new(emission_node.outputs[0], mix_node.inputs[1])
                            links.new(transparent_node.outputs[0], mix_node.inputs[2])

                            emission_node.inputs[0].default_value = (1, 1, 1, 1)
                            emission_node.inputs[1].default_value = 10

    # Also make ceilings slightly emit light
    elif obj.name.startswith("Ceiling#"):
        for m in obj.material_slots:
            nodes = m.material.node_tree.nodes
            links = m.material.node_tree.links

            output = nodes.get("Material Output")
            emission = nodes.get("Emission")
            if emission is None:
                diffuse = nodes.get("Diffuse BSDF")
                if diffuse is not None:
                    mix_node = nodes.new(type='ShaderNodeMixShader')
                    lightPath_node = nodes.new(type='ShaderNodeLightPath')
                    emission_node = nodes.new(type='ShaderNodeEmission')

                    link = next(l for l in links if l.from_socket == diffuse.outputs[0])
                    to_socket = link.to_socket
                    links.remove(link)

                    links.remove(next(l for l in links if l.to_socket == output.inputs[0]))
                    links.new(mix_node.outputs[0], output.inputs[0])

                    links.new(lightPath_node.outputs[0], mix_node.inputs[0])
                    links.new(emission_node.outputs[0], mix_node.inputs[1])
                    links.new(diffuse.outputs[0], mix_node.inputs[2])

                    emission_node.inputs[1].default_value = 1.5

# Remove all material nodes except diffuse and emission shader
# This reduces the rendering time but could be removed to increase the rendering quality
for mat in bpy.data.materials:
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output = nodes.get("Material Output")
    if nodes.get("Emission") is None:
        diff = nodes.get("Diffuse Shader")
        if diff is None:
            diff = nodes.get("Diffuse BSDF")
        if diff is None:
            diff = nodes.get("Diff BSDF")

        if diff is not None:
            link = next(l for l in links if l.to_socket == output.inputs[0])
            links.remove(link)
            links.new(diff.outputs[0], output.inputs[0])

# Open cam file, go through all poses and render from every view
with open(cam_file) as f:
    camPoses = f.readlines()

    for i, camPos in enumerate(camPoses):
        if cam_ids is None or i in cam_ids:
            camArgs = [float(x) for x in camPos.strip().split()]
            cam_ob.location = mathutils.Vector([camArgs[0], -camArgs[2], camArgs[1]])

            rot_quat = mathutils.Vector([camArgs[3], -camArgs[5], camArgs[4]]).to_track_quat('-Z', 'Y')
            cam_ob.rotation_euler = rot_quat.to_euler()
            cam.lens_unit = 'FOV'
            cam.angle = camArgs[9] * 2
            cam.clip_start = 1

            if started_from_commandline:
                scene.render.filepath = output_dir + "/" + str(i) + ".png"
                bpy.ops.render.render(write_still=True)
            else:
                break
