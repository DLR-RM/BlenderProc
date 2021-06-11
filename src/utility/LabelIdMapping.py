import csv

class LabelIdMapping:
	""" Handles category id mapping for semantic segmentation maps. """

	def __init__(self):
		# maps from an id to its name. E.g. id_label_map[0] = "void"
		self._id_label_map = {}
		# maps a class/category name to its id. E.g. label_id_map["void"] = 0
		self._label_id_map = {}
		self._num_ids = 0

	@staticmethod
	def from_file(path, label_col_name="name", id_col_name="id"):
		with open(path, 'r') as csvfile:
			reader = csv.DictReader(csvfile)
			mapping = LabelIdMapping()

			for row in reader:
				mapping.add(row[label_col_name], int(row[id_col_name]))

			return mapping

	def add(self, label, id):
		self._id_label_map[id] = label
		self._label_id_map[label] = id
		self._num_ids = max(self._num_ids, id + 1)

	def id_from_label(self, label):
		return self._label_id_map[label]

	def label_from_id(self, id):
		return self._id_label_map[id]

	def has_label(self, label):
		return label in self._id_label_map

	def has_id(self, label):
		return label in self._id_label_map