# Debugging

To find a bug or to understand what the pipeline is doing, it is possible to run BlenderProc from inside Blender.
Beforehand the config should have been run at least once via the `run.py` script to make sure the correct blender version and the required additional python packages are installed.


To start the pipeline from inside Blender, the `src/debug.py` script has to be opened and executed in Blender's scripting tab:

![alt text](blender.png)

Per default this loads and runs the config file located in `examples/debugging/config.yaml`.
As blender does not allow passing arguments to the script, all paths need to be defined inside the configuration file. 