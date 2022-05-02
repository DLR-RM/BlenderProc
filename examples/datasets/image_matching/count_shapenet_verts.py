import csv
from pathlib import Path
import trimesh
shapenet_dir = Path("/media/domin/data/shapenet/ShapeNetCore.v2/")
from tqdm import tqdm

sdfsd
with open('examples/datasets/image_matching/shapenet_verts.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["type", "model_id", "triangles"])
    for obj_type in tqdm(list(shapenet_dir.iterdir())):
        if obj_type.is_dir():
            for model in tqdm(list(obj_type.iterdir()), leave=False):
                if (model / "models" / "model_normalized.obj").exists():
                    mesh = trimesh.load_mesh(str(model / "models" / "model_normalized.obj"))
                    writer.writerow([obj_type.name, model.name, len(mesh.triangles)])


