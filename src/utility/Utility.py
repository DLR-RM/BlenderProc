import os
import bpy
import time

class Utility:
    working_dir = ""

    @staticmethod
    def resolve_path(path):
        """ Returns absolute path. If given path is relative, current working directory is put in front. """
        path = path.strip()

        if path.startswith("/"):
            return path
        else:
            return os.path.join(os.path.dirname(Utility.working_dir), path)

    @staticmethod
    def merge_dicts(source, destination):
        """ Recursively copies all key value pairs from src to dest (Overwrites existing) """
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                Utility.merge_dicts(value, node)
            else:
                destination[key] = value

        return destination

    @staticmethod
    def hex_to_rgba(hex):
        return [x / 255 for x in bytes.fromhex(hex[-6:])] + [1.0]

    @staticmethod
    def insert_node_instead_existing_link(links, source_socket, new_node_dest_socket, new_node_src_socket, dest_socket):
        for l in links:
            if l.from_socket == source_socket or l.to_socket == dest_socket:
                links.remove(l)

        links.new(source_socket, new_node_dest_socket)
        links.new(new_node_src_socket, dest_socket)

    class BlockStopWatch:
        """ Usage: with BlockStopWatch('text'): """
        def __init__(self, block_name):
            self.block_name = block_name

        def __enter__(self):
            print("#### Start - " + self.block_name + " ####")
            self.start = time.time()

        def __exit__(self, type, value, traceback):
            print("#### Finished - " + self.block_name + " (took " + ("%.3f" % (time.time() - self.start)) + " seconds) ####")

    class UndoAfterExecution:
        """ Usage: with UndoAfterExecution(): """

        def __enter__(self):
            bpy.ops.ed.undo_push(message="before")

        def __exit__(self, type, value, traceback):
            bpy.ops.ed.undo_push(message="after")
            # The current state points to "after", now by calling undo we go back to "before"
            bpy.ops.ed.undo()
