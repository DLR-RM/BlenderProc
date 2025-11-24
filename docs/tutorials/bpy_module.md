# Using `bpy` module from pip

BlenderProc supports using `bpy` module installed from pip. This behavior is controlled using the `USE_EXTERNAL_BPY_MODULE=1` environment variable.

## Setup

1. Set `USE_EXTERNAL_BPY_MODULE=1` in your environment
2. `pip install bpy==4.2.0`
3. Install [required packages](#required-dependencies)
4. After `import blenderproc` call `blenderproc.init()`
5. Run your script using `python my_script.py` or `blenderproc run my_script.py`

## Limitations
- BlenderProc Blender dependencies have to be installed manually, see [required dependencies](#required-dependencies).
- **Requires Python** version **3.11** - this is bound to the version `bpy` and Blender uses, it is the Python version suggested by [VFX Reference Platform](https://vfxplatform.com/).
- All [limitations](https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html#limitations) of the `bpy` module itself.
- `blenderproc debug` command is not available, as `bpy` module does not support user interface.
- `blenderproc pip` commands are not available. Use the `pip` commands in your environment instead.

## Required dependencies
Following dependencies have to be installed in your environment to allow using BlenderProc with Python `bpy` module. 

```
pip install wheel bpy==4.2.0 pyyaml==6.0.1 imageio==2.34.1 gitpython==3.1.43 scikit-image==0.23.2 pypng==0.20220715.0 scipy==1.13.1 matplotlib==3.9.0 pytz==2024.1 h5py==3.11.0 Pillow==10.3.0 opencv-contrib-python==4.10.* scikit-learn==1.5.0 python-dateutil==2.9.0.post0 rich==13.7.1 trimesh==4.4.0 pyrender==0.1.45 PyQT5
```

This is because BlenderProc does not require these dependencies directly, but the Blender it uses does. When using `bpy` package there is no Blender being installed and these dependencies become dependencies of the BlenderProc.

## Troubleshooting

### Python version mismatch

```
pip install bpy==4.2.0
Defaulting to user installation because normal site-packages is not writeable
ERROR: Ignored the following versions that require a different python version: 2.82.1 Requires-Python >=3.7, <3.8
ERROR: Could not find a version that satisfies the requirement bpy==4.2.0 (from versions: none)
ERROR: No matching distribution found for bpy==4.2.0
```

Using BlenderProc with `bpy` module from pip strictly requires Python3.11, see [Limitations](#limitations). Suggested workflow is to work with virtual environment using Python3.11. 

```
python --version
Python 3.11 X

python -m venv "venv"
```

Then install [Required Dependencies](#required-dependencies).