
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
    default_pip_packages = ["wheel", "pyyaml==5.1.2", "imageio==2.9.0", "gitpython==3.1.18", "scikit-image==0.18.3", "pypng==0.0.20", "scipy==1.7.1",
                            "matplotlib==3.4.3", "pytz==2021.1", "h5py==3.4.0", "Pillow==8.3.2", "opencv-contrib-python==4.5.3.56", "scikit-learn==0.24.2"]