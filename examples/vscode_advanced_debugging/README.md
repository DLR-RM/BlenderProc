# Advanced Debugging with VSCode

Contributor: [zhezh](https://github.com/zhezh/BlenderProc)

In this example, we will describe how to debug the python code executed by Blender's python interpreter, e.g.  `src/run.py` which can not be debugged directly in PyCharm or an other IDE. Although, we focus on debugging with the Blender's python interpreter, this method is general.

## Preparation
- This tutorial is aimed for debugging in: [VSCode](https://code.visualstudio.com/Download)
- [ptvsd](https://github.com/microsoft/ptvsd), the python package, which we are going to use, the installation is part of the tutorial.
- [examples/basic](https://github.com/DLR-RM/BlenderProc/tree/master/examples/basic) Make sure you have run this example before, our debugging example is based on this `basic` example.

## Steps
Firstly, open VSCode and click `File->OpenFolder` to open this repo. Then take a look at `examples/basic/config.yaml`. We have added `ptvsd` into `setup / pip`.

Secondly, insert below snippet at the 20th line of `src/run.py`, just below  `sys.path.append(packages_path)`, then add some breakpoints in `src/run.py`.
```python
import ptvsd
ptvsd.enable_attach()
ptvsd.wait_for_attach()
```

Thirdly, locate to `Debug and Run` tab as below image and create a `launch.json`. Delete all content in `launch.json` and paste below content into it.
![](vscode_debug.png)

```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Remote Attach",
            "type": "python",
            "request": "attach",
            "port": 5678,
            "host": "localhost",
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "."
                }
            ]
        },
    ]
}
```

Finally, execute below command in repo root directory
```bash
python run.py examples/vscode_advanced_debugging/config.yaml examples/basic/camera_positions examples/basic/scene.obj examples/vscode_advanced_debugging/output
```
and then start the debugger client in VSCode, enjoy debugging~

## Important Notice
- make sure the debugger is running, otherwise your app will halt
- add breakpoints after setting up ptvsd, otherwise the breakpoints will not take effect
- if error occurs when import ptvsd, check if you insert snippet in 2nd step correctly
