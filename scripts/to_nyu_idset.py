import numpy as np

old_suncg_id_label_map = ["" for i in range(37)]
nyu_id_label_map = ["" for i in range(41)]

old_suncg_label_id_map = {}
nyu_label_id_map = {}


old_suncg_id_label_map[0] = "void"
old_suncg_id_label_map[1] = "bed"
old_suncg_id_label_map[2] = "blinds"
old_suncg_id_label_map[3] = "books"
old_suncg_id_label_map[4] = "bookshelf"
old_suncg_id_label_map[5] = "cabinet"
old_suncg_id_label_map[6] = "ceiling"
old_suncg_id_label_map[6 + 1] = "chair"
old_suncg_id_label_map[7 + 1] = "clothes"
old_suncg_id_label_map[8 + 1] = "counter"
old_suncg_id_label_map[9 + 1] = "curtain"
old_suncg_id_label_map[10 + 1] = "desk"
old_suncg_id_label_map[11 + 1] = "door"
old_suncg_id_label_map[12 + 1] = "dresser"
old_suncg_id_label_map[13 + 1] = "floor"
old_suncg_id_label_map[14 + 1] = "floor_mat"
old_suncg_id_label_map[15 + 1] = "lamp"
old_suncg_id_label_map[16 + 1] = "mirror"
old_suncg_id_label_map[17 + 1] = "night_stand"
old_suncg_id_label_map[18 + 1] = "otherfurniture"
old_suncg_id_label_map[19 + 1] = "otherprop"
old_suncg_id_label_map[20 + 1] = "otherstructure"
old_suncg_id_label_map[21 + 1] = "person"
old_suncg_id_label_map[22 + 1] = "picture"
old_suncg_id_label_map[23 + 1] = "pillow"
old_suncg_id_label_map[24 + 1] = "refridgerator"
old_suncg_id_label_map[25 + 1] = "shelves"
old_suncg_id_label_map[26 + 1] = "shower_curtain"
old_suncg_id_label_map[27 + 1] = "sink"
old_suncg_id_label_map[28 + 1] = "sofa"
old_suncg_id_label_map[29 + 1] = "table"
old_suncg_id_label_map[30 + 1] = "television"
old_suncg_id_label_map[31 + 1] = "toilet"
old_suncg_id_label_map[32 + 1] = "bathtub"
old_suncg_id_label_map[33 + 1] = "wall"
old_suncg_id_label_map[34 + 1] = "whiteboard"
old_suncg_id_label_map[35 + 1] = "window"


nyu_id_label_map[0] = "void"
nyu_id_label_map[1] = "wall"
nyu_id_label_map[2] = "floor"
nyu_id_label_map[3] = "cabinet"
nyu_id_label_map[4] = "bed"
nyu_id_label_map[5] = "chair"
nyu_id_label_map[6] = "sofa"
nyu_id_label_map[7] = "table"
nyu_id_label_map[8] = "door"
nyu_id_label_map[9] = "window"
nyu_id_label_map[10] = "bookshelf"
nyu_id_label_map[11] = "picture"
nyu_id_label_map[12] = "counter"
nyu_id_label_map[13] = "blinds"
nyu_id_label_map[14] = "desk"
nyu_id_label_map[15] = "shelves"
nyu_id_label_map[16] = "curtain"
nyu_id_label_map[17] = "dresser"
nyu_id_label_map[18] = "pillow"
nyu_id_label_map[19] = "mirror"
nyu_id_label_map[20] = "floor_mat"
nyu_id_label_map[21] = "clothes"
nyu_id_label_map[22] = "ceiling"
nyu_id_label_map[23] = "books"
nyu_id_label_map[24] = "refridgerator"
nyu_id_label_map[25] = "television"
nyu_id_label_map[26] = "paper"
nyu_id_label_map[27] = "towel"
nyu_id_label_map[28] = "shower_curtain"
nyu_id_label_map[29] = "box"
nyu_id_label_map[30] = "whiteboard"
nyu_id_label_map[31] = "person"
nyu_id_label_map[32] = "night_stand"
nyu_id_label_map[33] = "toilet"
nyu_id_label_map[34] = "sink"
nyu_id_label_map[35] = "lamp"
nyu_id_label_map[36] = "bathtub"
nyu_id_label_map[37] = "bag"
nyu_id_label_map[38] = "otherstructure"
nyu_id_label_map[39] = "otherfurniture"
nyu_id_label_map[40] = "otherprop"

for i in xrange(len(old_suncg_id_label_map)):
	old_suncg_label_id_map[old_suncg_id_label_map[i]] = i

for i in xrange(len(nyu_id_label_map)):
	nyu_label_id_map[nyu_id_label_map[i]] = i


def suncg_to_nyu(label):
	nyu_label = np.zeros_like(label)
	unq = np.unique(label)

	for id in unq:
		label_name = old_suncg_id_label_map[id]
		nyu_id = nyu_label_id_map[old_suncg_id_label_map[id]]
		nyu_label[label == id] = nyu_id

	return nyu_label