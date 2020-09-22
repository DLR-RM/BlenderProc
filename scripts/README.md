# Scripts

Here we collect some useful scripts, to work with the in- or output of BlenderProc.

* [printHdf5Keys.py](printHdf5Keys.py): takes a hdf5 file or several as an argument and prints the used keys.
* [saveAsImg.py](saveAsImg.py): takes a hdf5 file or several as an argument and saves the image data in .jpg images.
* [visHdf5Files.py](visHdf5Files.py): takes a hdf5 file or several as an argument and visualizes them.
* [generate_nice_vis_rendering.py](generate_nice_vis_rendering.py): takes a hdf5 file or several as an argument and visualize the content in one image.
* [vis_coco_annotation.py](vis_coco_annotation.py): takes a coco .json file, image index and a path to a `coco_data/` folder of the generated data as arguments and visualizes the annotations for the specified image.
* [format_coco_annotations.py](format_coco_annotations.py): takes a coco .json file as an argument, deletes faulty annotations and saves as a new .json file.
* [find_missing_docu](find_missing_docu.py): prints out all docu-related issues (in regards to the .csv table contents at the module's docstring) present in any .py file in `scr/`.

Download scripts:
* [download_cc_textures.py](download_cc_textures.py): downloads all textures available on [cc0textures.com](http://cc0textures.com) and saves them under resources
* [download_scenenet.py](download_scenenet.py): downloads the data from SceneNet, the download link for the [texture]( http://tinyurl.com/zpc9ppb) is also provided.
* [download_pix3d.py](download_pix3d.py): downloads the data from Pix3D [website](http://pix3d.csail.mit.edu/).
