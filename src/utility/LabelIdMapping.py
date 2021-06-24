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
	def from_csv(path, label_col_name="name", id_col_name="id") -> "LabelIdMapping":
		""" Builds a label-id mapping based on the given csv file.

		:param path: The path to a csv file.
		:param label_col_name: The name of the column which should be used as label.
		:param id_col_name: The name of the column which should be used as id.
		:return: The built label mapping object.
		"""
		with open(path, 'r') as csvfile:
			reader = csv.DictReader(csvfile)
			mapping = LabelIdMapping()

			for row in reader:
				mapping.add(row[label_col_name], int(row[id_col_name]))

			return mapping

	@staticmethod
	def from_dict(label_to_id: dict) -> "LabelIdMapping":
		""" Builds a label-id mapping based on the given dict.

		:param label_to_id: A dict where keys are labels and values are ids.
		:return: The built label mapping object.
		"""
		mapping = LabelIdMapping()
		for label, id in label_to_id.items():
			mapping.add(label, id)
		return mapping

	def add(self, label: str, id: int):
		""" Inserts the given label-id pair into the mapping.

		:param label: The label of the pair.
		:param id: The id of the pair
		"""
		if self.has_id(id):
			raise Exception("There already exists a label-id mapping for the id " + str(id))
		if self.has_label(id):
			raise Exception("There already exists a label-id mapping for the label " + label)

		self._id_label_map[id] = label
		self._label_id_map[label] = id
		self._num_ids = max(self._num_ids, id + 1)

	def id_from_label(self, label: str):
		""" Returns the id assigned to the given label.

		:param label: The label to look for.
		:return: The id with the given label.
		"""
		return self._label_id_map[label]

	def label_from_id(self, id: int):
		""" Returns the label assigned to the given id.

		:param id: The id to look for.
		:return: The label with the given id.
		"""
		return self._id_label_map[id]

	def has_label(self, label: str):
		""" Checks if the mapping contains the given label.

		:param label: The label to look for.
		:return: True, if the label is already in use.
		"""
		return label in self._label_id_map

	def has_id(self, id: int):
		""" Checks if the mapping contains the given id.

		:param id: The id to look for.
		:return: True, if the id is already in use.
		"""
		return id in self._id_label_map