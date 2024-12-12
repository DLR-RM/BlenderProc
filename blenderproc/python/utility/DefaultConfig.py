""" All default values are stored here. """


class DefaultConfig:
    """
    All the default config values are specified in this class.
    """
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
    lens_unit = "FOV"

    # Stereo
    stereo_convergence_mode = "PARALLEL"
    stereo_convergence_distance = 0.00001
    stereo_interocular_distance = 0.065

    # Renderer
    file_format = "PNG"
    color_depth = 8
    enable_transparency = False
    jpg_quality = 95
    samples = 1024
    sampling_noise_threshold = 0.01
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
    antialiasing_distance_max = 10000
    world_background = [0.05, 0.05, 0.05]
    view_transform = "Filmic"
    look = None
    exposure = 0.0
    gamma = 1.0

    # Setup
    default_pip_packages = ["wheel", "pyyaml==6.0.1", "imageio==2.34.1", "gitpython==3.1.43",
                            "scikit-image==0.23.2", "pypng==0.20220715.0", "scipy==1.13.1", "matplotlib==3.9.0",
                            "pytz==2024.1", "h5py==3.11.0", "Pillow==10.3.0", "opencv-contrib-python==4.10.0.82",
                            "scikit-learn==1.5.0", "python-dateutil==2.9.0.post0", "rich==13.7.1", "trimesh==4.4.0",
                            "pyrender==0.1.45"]
