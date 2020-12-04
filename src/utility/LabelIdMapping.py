import csv

class LabelIdMapping(object):
	""" Handles category id mapping for semantic segmentation maps. It's used as a static Singleton class

	Attributes:
	id_label_map: maps from an id to its name. E.g. id_label_map[0] = "void".
	label_id_map: maps a class/category name to its id. E.g. label_id_map["void"] = 0.
	"""
	id_label_map = []
	label_id_map = {}

	def __init__(self):
		pass

	@staticmethod
	def read_csv_mapping(path):
		""" Loads an idset mapping from a csv file, assuming the rows are sorted by their ids.
		
		:param path: Path to csv file
		"""

		with open(path, 'r') as csvfile:
				reader = csv.DictReader(csvfile)
				new_id_label_map = []
				new_label_id_map = {}

				for row in reader:
					new_id_label_map.append(row["name"])
					new_label_id_map[row["name"]] = int(row["id"])

				return new_id_label_map, new_label_id_map

	@staticmethod
	def assign_mapping(mapping):
		""" Assign a mapping based on a given id-set. This mapping could be a path to a csv file holding the \
		id-set, or a tuple contaning the attributes that should be assigned to this class

		:param mapping: If string then it's assumed it's a csv file holding the mapping, otherwise a tuple \
						holding the values that should be assigned to the attributes id_label_map, label_id_map, \
						respectively.
		"""
		if isinstance(mapping, str):
			mapping = LabelIdMapping.read_csv_mapping(mapping)

		LabelIdMapping.id_label_map, LabelIdMapping.label_id_map = mapping
