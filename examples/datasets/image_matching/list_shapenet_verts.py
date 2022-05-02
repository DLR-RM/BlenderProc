import csv


with open('examples/datasets/image_matching/shapenet_verts.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    shapenets = []
    for row in reader:
        shapenets.append((row["type"] +"/"+ row["model_id"], int(row["triangles"])))

shapenets = sorted(shapenets, key=lambda x: x[-1], reverse=True)

for row in shapenets[:20]:
    print(row)
