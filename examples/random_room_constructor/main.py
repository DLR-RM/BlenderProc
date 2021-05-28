from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from src.utility.constructor.RandomRoomConstructor import RandomRoomConstructor
from src.utility.lighting.SurfaceLighting import SurfaceLighting
from src.utility.loader.CCMaterialLoader import CCMaterialLoader
from src.utility.loader.IKEALoader import IKEALoader
from src.utility.WriterUtility import WriterUtility
from src.utility.Initializer import Initializer

from src.utility.RendererUtility import RendererUtility
from src.utility.PostProcessingUtility import PostProcessingUtility

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('ikea_path', nargs='?', default="resources/ikea", help="Path to the downloaded IKEA dataset, see the /scripts for the download script")
parser.add_argument('cc_material_path', nargs='?', default="resources/cctextures", help="Path to CCTextures folder, see the /scripts for the download script.")
parser.add_argument('output_dir', nargs='?', default="examples/random_room_constructor/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

materials = CCMaterialLoader.load(args.cc_material_path, ["Bricks", "Wood", "Carpet", "Tile", "Marble"])
interior_objects = []
for i in range(15):
    interior_objects.extend(IKEALoader.load(args.ikea_path, ["bed", "chair", "desk", "bookshelf"]))

objects = RandomRoomConstructor.construct(25, interior_objects, materials, amount_of_extrusions=5)

SurfaceLighting.run([obj for obj in objects if obj.get_name() == "Ceiling"], emission_strength=4.0)

# activate distance rendering
RendererUtility.enable_normals_output()
# set the amount of samples, which should be used for the color rendering
RendererUtility.set_samples(350)
RendererUtility.set_light_bounces(max_bounces=200, diffuse_bounces=200, glossy_bounces=200, transmission_bounces=200, transparent_max_bounces=200)
# render the whole pipeline
data = RendererUtility.render()

# post process the data and remove the redundant channels in the distance image
data["depth"] = PostProcessingUtility.dist2depth(data["distance"])
del data["distance"]

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
