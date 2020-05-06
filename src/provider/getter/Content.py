from src.main.Provider import Provider

class Content(Provider):
    """ Returns the raw dictionary given to this Provider as content. Works as a wrapper layer between module and some
        input values.

        Example 1: Pass `content` dictionary to the EntityManipulator's `add_modifier` custom function.

        }
          "module": "manipulators.EntityManipulator",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "cp_shape_net_object": True,
                "type": "MESH"
              }
            },
            "cf_add_modifier": {
              "provider": "getter.Content",
              "content": {
                "name": "Solidify",
                "thickness": 0.001
              }
            }
          }
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "content", "The raw content which should be returned. Type: any data type."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        Returns the `content` config parameter value.
        """
        return self.config.get_raw_dict("content")
