# Writer

Writer can be used to pack all output produced by BlenderProc into a specific format.

## HDF5 Writer

By using `bproc.writer.write_hdf5`, all given data corresponding to the same frame is packed into one `.hdf5` file. 
This has the advantage that all data is compressed and the data of different frames cannot get mixed up.

To visualize a given hdf5 file, you can use BlenderProcs CLI:
```bash
blenderproc vis hdf5 <path_to_file>
```

If you want to read `.hdf5` files in your data processing code, you can make use of the `h5py` python package:

```python
import h5py
with h5py.File("myfile.hdf5") as f:
    colors = np.array(f["colors"])
```

To read in json strings saved in the hdf5 File (e.g. object poses), you can make use of the following snippet:

```python
text = np.array(f["object_states"]).tostring()
obj_states = json.loads(text)
```

## Coco Writer

Via `bproc_writer.write_coco_annotations`, rendered instance segmentations are written in the COCO format.
Read more about the specifications of this format [here](https://cocodataset.org/#format-data)

To visualize a frame written in the COCO format, you can use BlenderProcs CLI:
```bash
blenderproc vis coco <path_to_file>
```

## BOP Writer

With `bproc.writer.write_bop`, depth and RGB images, as well as camera intrinsics and extrinsics are stored in a BOP dataset.
Read more about the specifications of the BOP format [here](https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md)

--

Next tutorial: [How key frames work](key_frames.md)
