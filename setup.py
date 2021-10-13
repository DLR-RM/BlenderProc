from setuptools import setup, find_packages

setup(name='blenderproc',
      version='2.0.0a4',
      url='https://github.com/DLR-RM/BlenderProc',
      author='German Aerospace Center (DLR) - Institute of Robotics and Mechatronics (RM)',
      packages=find_packages(exclude=['docs', 'examples', 'external', 'images', 'resources', 'scripts', 'tests']),
      entry_points={
            'console_scripts': ['blenderproc=blenderproc.command_line:cli'],
      },
      install_requires=["setuptools", "pyyaml", "requests", "matplotlib", "numpy", "Pillow", "h5py"]
      )