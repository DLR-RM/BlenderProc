import bpy
import sys
from pathlib import Path

# Extract given arguments
argv = sys.argv[sys.argv.index("--") + 1:]

# Switch to scripting workspace
bpy.context.window.workspace = bpy.data.workspaces["Scripting"]
bpy.context.view_layer.update()

# Load text to put into scripting tool
is_config = not argv[0].endswith(".py")
if is_config:
    # Create a new temporary script based on debug.py
    text = bpy.data.texts.new("debug")
    with open(Path(__file__).with_name("debug.py")) as f:
        script_text = f.read()
        # Replace placeholders
        script_text = script_text.replace("###CONFIG_PATH###", argv[0])
        script_text = script_text.replace("[\"###CONFIG_ARGS###\"]", str(argv[2:]))
        # Put into blender text object
        text.from_string(script_text)
    # Set cursor to the beginning
    text.cursor_set(0)
    # Set filepath such that it can be used inside debug.py, while not overwriting it
    text.filepath = str(Path(__file__).with_name("debug_temp.py").absolute())
else:
    # Just load python script into blender text object
    text = bpy.data.texts.load(argv[0])

# Put text into scripting tool
for area in bpy.data.workspaces["Scripting"].screens[0].areas.values():
    if area.type == 'TEXT_EDITOR':
        area.spaces.active.text = text

# Set script arguments
sys.argv = ["debug"] + argv[2:]