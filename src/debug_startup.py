import bpy
import sys

argv = sys.argv[sys.argv.index("--") + 1:]
bpy.context.window.workspace = bpy.data.workspaces["Scripting"]
bpy.context.view_layer.update()

text = bpy.data.texts.load(argv[0])
for area in bpy.data.workspaces["Scripting"].screens[0].areas.values():
    if area.type == 'TEXT_EDITOR':
        area.spaces.active.text = text

sys.argv = ["debug"] + argv[2:]
print(sys.argv)