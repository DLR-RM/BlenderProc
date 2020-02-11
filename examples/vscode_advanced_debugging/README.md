# Advanced Debugging with VSCode

Contributor: [zhezh](https://github.com/zhezh/BlenderProc)

In this example, we will describe how to debug the python code executed by Blender's python interpretor, e.g.  `src/run.py` which can not be debugged directly in PyCharm or other IDE. Although we focus on debugging with Blender, this method is general.

## Preparation
- [VSCode](https://code.visualstudio.com/Download)
- [ptvsd](https://github.com/microsoft/ptvsd) We will illustrate how to install it in next step.
- [examples/basic](https://github.com/DLR-RM/BlenderProc/tree/master/examples/basic) Make sure you have tried this example.

## Steps
Firstly, add `ptvsd` into `setup / pip` of `examples/basic/config.yaml`. The first few lines should be like below:
```
{
  "version": 2,
  "setup": {
    "blender_install_path": "/home_local/<env:USER>/blender/",
    "pip": [
      "h5py",
      "ptvsd"
    ]
  },
```

Then, insert below snippet at 6th line of `src/run.py` (below last import)
```python
import ptvsd
ptvsd.enable_attach()
ptvsd.wait_for_attach()
```

Finally, open VSCode and click `File->OpenFolder` to open this repo.

![](vscode_debug.png)

Then locate to `Debug and Run` tab as above image and create a `launch.json`. Delete all content in `launch.json` and paste below content into it.

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

Add some breakpoints in `src/run.py`, run the basic example and then start the debugger client in VSCode, enjoy debugging~



## Important Notice
- make sure the debugger is running, otherwise your app will halt
- add breakpoints after setting up ptvsd, otherwise the breakpoints will not work
- ...