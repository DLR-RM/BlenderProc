# Kinect Azure Noise

<p align="center">
<img src="../../../images/kinect_azure_rendering_1.png" alt="Front readme image" width=375>
<img src="../../../images/kinect_azure_rendering_0.png" alt="Front readme image" width=375>
</p>

In this example we apply kinect azure noise postprocessing to our rendered depth maps.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/kinect_azure_noise/main.py examples/resources/camera_positions examples/resources/scene.obj examples/advanced/kinect_azure_noise/output
```

* `examples/advanced/kinect_azure_noise/main.py`: path to the python file with pipeline configuration.

The three arguments afterwards are used by the `argparser` at the top of the `main.py` file:
* `examples/resources/camera_positions`: text file with parameters of camera positions.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/kinect_azure_noise/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/advanced/kinect_azure_noise/output/0.hdf5
```

## Implementation

```python
data["depth"] = bproc.postprocessing.add_kinect_azure_noise(data["depth"], data["colors"])
```

* Generates depth maps that immitate the kinect azure sensor data. Color data is used to create missing depth at dark surfaces.




