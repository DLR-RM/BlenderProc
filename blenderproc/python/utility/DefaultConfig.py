
class DefaultConfig:
    # Camera
    resolution_x = 512
    resolution_y = 512
    clip_start = 0.1
    clip_end = 1000
    fov = 0.691111
    pixel_aspect_x = 1
    pixel_aspect_y = 1
    shift_x = 0
    shift_y = 0

    # Stereo
    stereo_convergence_mode = "PARALLEL"
    stereo_convergence_distance = 0.00001
    stereo_interocular_distance = 0.065

    # Renderer
    samples = 100
    cpu_threads = 1
    denoiser = "INTEL"
    simplify_subdivision_render = 3
    diffuse_bounces = 3
    glossy_bounces = 0
    ao_bounces_render = 3
    max_bounces = 3
    transmission_bounces = 0
    transparency_bounces = 8
    volume_bounces = 0

    # Setup
    default_pip_packages = ["wheel", "pyyaml==5.1.2", "imageio", "gitpython", "scikit-image", "pypng==0.0.20", "scipy",
                            "matplotlib", "pytz", "h5py", "Pillow", "opencv-contrib-python", "Pillow", "scikit-learn"]