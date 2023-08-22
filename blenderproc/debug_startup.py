""" This script allows the use of the debug mode in BlenderProc. """

import sys
import os

import bpy
from bl_ui.space_text import TEXT_MT_editor_menus

# Extract given arguments
argv = sys.argv[sys.argv.index("--") + 1:]

# Switch to scripting workspace
bpy.context.window.workspace = bpy.data.workspaces["Scripting"]
bpy.context.view_layer.update()

# Just load python script into blender text object
text = bpy.data.texts.load(os.path.abspath(argv[0]))


# Declare operator that runs the blender proc script
class RunBlenderProcOperator(bpy.types.Operator):
    """ This operator adds the Run BlenderProc button to the GUI """

    bl_idname = "wm.run_blenderproc"
    bl_label = "Run BlenderProc"
    bl_description = "This operator runs the loaded BlenderProc script and also makes sure to unload all " \
                     "modules before starting."
    bl_options = {"REGISTER"}

    def execute(self, _):
        """
        Execute the button -> running BlenderProc
        """
        # Delete all loaded models inside src/, as they are cached inside blender
        for module in list(sys.modules.keys()):
            if module.startswith("blenderproc") and module not in ["blenderproc.python.utility.SetupUtility"]:
                del sys.modules[module]

        # Make sure the parent of the blenderproc folder is in sys.path
        import_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if import_path not in sys.path:
            sys.path.append(import_path)

        # Run the script
        try:
            bpy.ops.text.run_script()
        except RuntimeError:
            # Skip irrelevant error messages (The relevant stacktrace+error has already been printed at this point)
            pass
        return {"FINISHED"}


bpy.utils.register_class(RunBlenderProcOperator)


# Declare function for drawing the header toolbar of the scripting area
# Mostly copied from blenders script: scripts/startup/bl_ui/space_text.py
def draw(self, context):
    """ Draws the newly defined Run BlenderProc button """
    layout = self.layout

    st = context.space_data
    context_text = st.text
    is_syntax_highlight_supported = st.is_syntax_highlight_supported()
    layout.template_header()

    TEXT_MT_editor_menus.draw_collapsible(context, layout)

    if context_text and context_text.is_modified:
        row = layout.row(align=True)
        row.alert = True
        row.operator("text.resolve_conflict", text="", icon='HELP')

    layout.separator_spacer()

    row = layout.row(align=True)
    row.template_ID(st, "text", new="text.new",
                    unlink="text.unlink", open="text.open")

    if context_text:
        is_osl = context_text.name.endswith((".osl", ".osl"))
        if is_osl:
            row.operator("node.shader_script_update",
                         text="", icon='FILE_REFRESH')
        else:
            row = layout.row()
            row.active = is_syntax_highlight_supported
            # The following line has changed compared to the orignal code,
            # it starts our operator instead of text.run_script
            row.operator("wm.run_blenderproc", text="Run BlenderProc")

    layout.separator_spacer()

    row = layout.row(align=True)
    row.prop(st, "show_line_numbers", text="")
    row.prop(st, "show_word_wrap", text="")

    syntax = row.row(align=True)
    syntax.active = is_syntax_highlight_supported
    syntax.prop(st, "show_syntax_highlight", text="")


# Set our draw function as the default draw function for text area headers
bpy.types.TEXT_HT_header.draw = draw

# Put text into scripting tool
for area in bpy.data.workspaces["Scripting"].screens[0].areas.values():
    if area.type == 'TEXT_EDITOR':
        area.spaces.active.text = text

# Set script arguments
sys.argv = ["debug"] + argv[2:]
