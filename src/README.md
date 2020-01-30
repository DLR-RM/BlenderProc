# Src code

Each module used in BlenderProc is defined in here. The folders structure the modules according to their use-case.

The [main](main) folder contains the Module base class and the Pipeline class, which gets executed by the run.py & debug.py

If you want to add new modules, we generally split our modules into different parts:
* [camera](camera): camera loading and pose sampling 
* [lighting](lighting): light loading and sampling, and dataset specific light loaders
* [loader](loader): loader for objects of .ply or .obj or for specific datasets
* [object](object): object pose manipulations, with physics or with sampling and geometry manipulation can be found here
* [renderer](renderer): all kind of renderers are defined here
* [utility](utility): several comfort functions to make the work with BlenderProc simpler
* [writer](writer): contains the state writers to save the state of the world into a .hdf5 container
* [composite](composite): modules, which use more than one other module to work
* [postprocessing](postprocessing): modules, which can be used in the .hdf5 writer to change the blender results

