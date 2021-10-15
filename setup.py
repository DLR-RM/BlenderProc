from setuptools import setup, find_packages
import os

# Extract version from blenderproc/version.py
here = os.path.abspath(os.path.dirname(__file__))
version = {}
with open(os.path.join(here, "blenderproc", "version.py")) as fp:
    exec(fp.read(), version)

with open(os.path.join(here, "README.md")) as fp:
      long_description = fp.read()

setup(name='blenderproc',
      version=version['__version__'],
      url='https://github.com/DLR-RM/BlenderProc',
      author='German Aerospace Center (DLR) - Institute of Robotics and Mechatronics (RM)',
      packages=find_packages(exclude=['docs', 'examples', 'external', 'images', 'resources', 'scripts', 'tests']),
      entry_points={
            'console_scripts': ['blenderproc=blenderproc.command_line:cli'],
      },
      install_requires=["setuptools", "pyyaml", "requests", "matplotlib", "numpy", "Pillow", "h5py", "progressbar"],
      long_description=long_description,
      long_description_content_type='text/markdown'
      )
