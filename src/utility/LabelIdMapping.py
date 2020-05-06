import csv

class LabelIdMapping(object):

	id_label_map = []
	label_id_map = {}
	num_labels   = 0

	def __init__(self):
		pass

	@staticmethod
	def read_csv_mapping(path):
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
		if isinstance(mapping, str):
			mapping = LabelIdMapping.read_csv_mapping(mapping)

		LabelIdMapping.id_label_map, LabelIdMapping.label_id_map = mapping
		LabelIdMapping.num_labels = len(LabelIdMapping.label_id_map)
