from sys import path
import os

import numpy as np
path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.utility.LabelIdMapping import LabelIdMapping

def switch_mapping(segmap, source_map, destination_map):
	# This assumes label names in different mappings are the same.
	# This function is mainly useful to map from the old class mapping to the now default NYU mapping.
	source_label_map = LabelIdMapping.from_csv(source_map)
	destination_label_map = LabelIdMapping.from_csv(destination_map)

	new_segmap = np.zeros_like(segmap)
	unq = np.unique(segmap)

	for id in unq:
		label_name = source_label_map.label_from_id(id)
		if destination_label_map.has_label(label_name):
			destination_id = destination_label_map.id_from_label(source_label_map.label_from_id(id))
			new_segmap[segmap == id] = destination_id

	return new_segmap

def old_mapping_to_nyu(segmap):
	return switch_mapping(segmap, os.path.join('resources', 'id_mappings', 'nyu_idset.csv'), 
		os.path.join('resources', 'id_mappings', 'old_idset.csv'))
