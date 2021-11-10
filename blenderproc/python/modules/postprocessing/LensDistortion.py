from blenderproc.python.modules.main.Module import Module
from blenderproc.python.camera.LensDistortionUtility import apply_lens_distortion


class LensDistortion(Module):
    """ This module can be used to postprocess images to apply a certain lens distortion, we rely here on the values:

            k1, k2, k3 and p1, p2

        Here k_n are the radial distortion parameters (of 3rd, 5th, and 7th degree in radial distance) as defined
        by the undistorted-to-distorted Brown-Conrady lens distortion model, which is conform to the current
        DLR CalLab/OpenCV/Bouguet/Kalibr implementations. The use of k_3 is discouraged unless the angular
        field of view is too high, rendering it necessary, and the parameter allows for a distorted projection in
        the whole sensor size (which isn't always given by features-driven camera calibration).
        Note that undistorted-to-distorted means that the distortion parameters are multiplied by undistorted,
        normalized camera projections to yield distorted projections, that are in turn digitized by the intrinsic
        camera matrix.

        p_n are the first and second decentering distortion parameters as proposed in (Conrady, 1919) and
        defended by Brown since 1965, and are comform to the current DLR CalLab/OpenCV/Bouguet/Kalibr
        implementations. This parameters share one degree of freedom (j1) with each other; as a
        consequence, either both parameters are given or none. The use of these parameters is discouraged,
        since either current cameras do not need them or their potential accuracy gain is negligible w.r.t.
        image processing.

        For more information see: https://en.wikipedia.org/wiki/Distortion_(optics)
        Note that, unlike in that wikipedia entry as of early 2021, we're here using the undistorted-to-distorted
        formulation.
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        """
        :param image: The image data.
        :return: The lens distorted image data.
        """
        return apply_lens_distortion(image), key, version
