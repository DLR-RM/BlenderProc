import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.filter.Filter import Filter
from blenderproc.python.utility.MathUtility import MathUtility
from blenderproc.python.sampler.UpperRegionSampler import UpperRegionSampler
from blenderproc.python.object.PhysicsSimulation import PhysicsSimulation
from blenderproc.python.sampler.PartSphere import PartSphere
from blenderproc.python.utility.Initializer import Initializer

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('shape_net', help="path to the downloaded shape net core v2 dataset, get it from (http://www.shapenet.org/)")
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/shapenet_with_suncg/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load suncg house into the scene
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))
suncg_objs = bproc.loader.load_suncg(args.house, label_mapping=label_mapping)

# Find all bed objects, to sample the shapenet objects on
bed_objs = Filter.by_cp(suncg_objs, "category_id", label_mapping.id_from_label("bed"))

# makes Suncg objects emit light
bproc.lighting.light_suncg_scene()

# load selected shapenet object
shapenet_obj = bproc.loader.load_shapenet(args.shape_net, used_synset_id="02801938")

# Sample a point above any bed
sample_point = UpperRegionSampler.sample(
    objects_to_sample_on=bed_objs,
    min_height=0.75,
)
# move the shapenet object to the sampled position
shapenet_obj.set_location(sample_point)

# adding a modifier we avoid that the objects falls through other objects during the physics simulation
shapenet_obj.add_modifier(name="SOLIDIFY", thickness=0.001)

# enable rigid body component of the objects which makes them participate in physics simulations
shapenet_obj.enable_rigidbody(active=True, mass_factor=2000, collision_margin=0.0001)
for obj in Filter.all_with_type(suncg_objs, MeshObject):
    obj.enable_rigidbody(active=False, mass_factor=2000, collision_margin=0.0001)

# Run the physics simulation
PhysicsSimulation.simulate_and_fix_final_poses(min_simulation_time=0.5, max_simulation_time=4, check_object_interval=0.25)

# sample five camera poses
for i in range(5):
    # sample random camera location around the shapenet object
    location = PartSphere.sample(center=shapenet_obj.get_location(), mode="SURFACE", radius=2, dist_above_center=0.5)
    # compute rotation based on vector going from the camera location towards shapenet object
    rotation_matrix = bproc.camera.rotation_from_forward_vec(shapenet_obj.get_location() - location)
    # add homog cam pose based on location an rotation
    cam2world_matrix = MathUtility.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)

# set the number of samples to render for each object
bproc.renderer.set_samples(150)

# activate normal and distance rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_distance_output()

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
