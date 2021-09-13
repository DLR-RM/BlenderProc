from setuptools import setup

setup(name='blenderproc',
      version='1.12',
      url='https://github.com/DLR-RM/BlenderProc',
      author='German Aerospace Center (DLR) - Institute of Robotics and Mechatronics (RM)',
      packages=['blenderproc'],
      entry_points={
            'console_scripts': ['blenderproc=blenderproc.command_line:cli'],
      })