
class Provider:
    """ A provider returns parameter values dynamically based on its configuration. """

    def __init__(self, config):
        self.config = config

    def run(self):
        raise NotImplementedError("Please implement this method")