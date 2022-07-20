# How key frames work

Blender as well as BlenderProc uses key frames to render multiple images in one render call.
This makes rendering the same scene with e.g. only different camera poses faster, as meshes have to be moved to the graphics card only once.

## Concept

When calling `bproc.renderer.render()` blender will go over all keyframes in the interval `[frame_start, frame_end - 1]` and render the scene once for each keyframe.
Thereby, each key frame can be assigned to different attribute values, e.g. camera or object poses, which will be set set when the respective key frame is rendered.

### Camera

In the beginning, `frame_start` and `frame_end` are both set to `0`.
When calling `bproc.camera.add_camera_pose(matrix_world)`, automatically a new key frame is added (`frame_end` is increased by `1`) and the given camera pose is assigned to it.
You can also set the camera pose to a specific key frame `i` via `bproc.camera.add_camera_pose(matrix_world, i)`, which will increase `frame_end` if necessary.

### Objects

When setting object poses, e.g. via `obj.set_location(location)` they are by default set for all key frames.
If you want to assign object poses to a specific frame `i`, you can make use of the `frame` parameter: `obj.set_location(location, frame=i)`.

## Debugging

To inspect which keyframes are actually set, it is possible to view them in BlenderProcs debug mode (Read the [quick start](../../README.md#quickstart) to find out how to get into debug mode).
After running you script in debug mode switch to the `Layout` tab:

In the layout tab you should see the `Timeline` area in the lower half of blender. 
In that area you should see the keyframes of the currently active object.
Perform a left click on the camera in the 3D view to see all registered camera poses.
Every registered keyframe is visualized via a yellow marker.


You can change the current active frame by moving the blue playhead or by setting the number next to start/end in the right top corner.
The 3D view always shows the scene in the state assigned to the current active frame (Press Numpad0 to see the scene from the current camera view).

## Render multiple times

It is possible to render multiple times in one session.
The only thing one has to remember is to remove all keyframes at the beginning of each run which can be done by calling `bproc.utility.reset_keyframes()`

So, lets say you have the following structure in your python script:

```
<object loading>

<light setting>

<setting random object poses>

<camera sampling>

<rendering>

<writing to file>
```

To now do the camera/object pose sampling and the rendering multiple times in one run, simply adjust the script in the following way:

```
<object loading>

<light creation>

for r in range(NUM_RUNS):
    bproc.utility.reset_keyframes()
    
    <setting random object poses>

    <setting random light poses & strengths>
    
    <camera sampling>
    
    <rendering>
    
    <writing to file>
```

Other properties such as object materials can not be keyframed so all images of one render path will contain the same materials. For these properties, it's better to call the rendering function frequently with a single or few keyframes and manipulate between the render calls.

--- 

Next tutorial: [Positioning objects via the physics simulator](physics.md)
