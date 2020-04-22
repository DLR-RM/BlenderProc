
from src.main.Provider import Provider

class Content(Provider):
    """
    The Content provider might be useful if you only want to return the content of something in the config file.
    Instead of it being directly used as a provider value.

    Example:

      "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "cp_shape_net_object": True,
            "type": "MESH"
          }
        },
        "cf_add_modifier": {  # this add modifier expects a dictionary with the content
          "provider": "getter.Content", # this provider will return this dictionary
          "content": {
            "name": "Solidify",
            "thickness": 0.001
          }
        }
    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "content", "The raw content which should be returned, can be anything."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        Returns the `content` of the given config
        """
        return self.config.get_raw_dict("content")
