import subprocess
import sys
import os

# this sets the amount of runs, which are performed
amount_of_runs = 5

# set the folder in which the cli.py is located
rerun_folder = os.path.abspath(os.path.dirname(__file__))

# the first one is the rerun.py script, the last is the output
used_arguments = sys.argv[1:-1]
output_location = os.path.abspath(sys.argv[-1])
for run_id in range(amount_of_runs):
    # in each run, the arguments are reused
    cmd = ["python", os.path.join(rerun_folder, "cli.py")]
    cmd.extend(used_arguments)
    # the only exception is the output, which gets changed for each run, so that the examples are not overwritten
    cmd.append(os.path.join(output_location, str(run_id)))
    print(" ".join(cmd))
    # execute one BlenderProc run
    subprocess.call(" ".join(cmd), shell=True)






