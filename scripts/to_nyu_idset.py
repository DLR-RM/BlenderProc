from sys import path
import os

import numpy as np
path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.utility.LabelIdMapping import LabelIdMapping

def switch_mapping(segmap, source_map, destination_map):
	# This assumes label names in different mappings are the same.
	# This function is mainly useful to map from the old class mapping to the now default NYU mapping.
	source_id_label_map, source_label_id_map = LabelIdMapping.read_csv_mapping(source_map)
	destination_id_label_map, destination_label_id_map = LabelIdMapping.read_csv_mapping(destination_map)

	new_segmap = np.zeros_like(segmap)
	unq = np.unique(segmap)

	for id in unq:
		label_name = source_id_label_map[id]
		if label_name in destination_label_id_map:
			destination_id = destination_label_id_map[source_id_label_map[id]]
			new_segmap[segmap == id] = destination_id

	return new_segmap

def old_mapping_to_nyu(segmap):
	return switch_mapping(segmap, os.path.join('resources', 'id_mappings', 'nyu_idset.csv'), 
		os.path.join('resources', 'id_mappings', 'old_idset.csv'))
