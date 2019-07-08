import os
import bpy
import time

class Utility:

    @staticmethod
    def resolve_path(path):
        path = path.strip()

        if path.startswith("/"):
            return path
        else:
            return os.path.join(os.path.dirname(bpy.data.filepath), path)

    @staticmethod
    def merge_dicts(source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                Utility.merge_dicts(value, node)
            else:
                destination[key] = value

        return destination

    class BlockStopWatch:
        def __init__(self, block_name):
            self.block_name = block_name

        def __enter__(self):
            print("#### Start - " + self.block_name + " ####")
            self.start = time.time()

        def __exit__(self, type, value, traceback):
            print("#### Finished - " + self.block_name + " (took " + ("%.3f" % (time.time() - self.start)) + " seconds) ####")
