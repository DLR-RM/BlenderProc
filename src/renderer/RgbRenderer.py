from src.renderer.Renderer import Renderer


class RgbRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)

    def run(self):
        self._configure_renderer()
        self._render("rgb_")
