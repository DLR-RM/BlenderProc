import h5py
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import argparse
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

parser = argparse.ArgumentParser(description="")
parser.add_argument('path')
args = parser.parse_args()

path = Path(args.path)

images = []
matchings = []
for file in sorted(path.rglob("*.hdf5"), key=lambda x: int(x.name[:-len(".hdf5")])):
    print(file)
    with h5py.File(file, "r") as f:
        images.append(np.array(f["colors"]))
        matchings.append(np.array(f["matching"]))

img1 = 1
img2 = 0
N = 2
offset = 3

matchings = matchings[offset * N:]
images = images[offset * N:]

print(matchings[img2].shape)
plt.imshow(np.repeat(np.concatenate((np.isnan(matchings[img2][img1%N - (1 if img1 > img2 else 0)]).any(-1)[..., None] * 255, np.isnan(matchings[img1][img2%N - (1 if img2 > img1 else 0)]).any(-1)[..., None] * 255), 1), 3, -1).astype(np.uint8))
plt.figure()

point = [0,0]
def draw():
    plt.clf()
    #print(matchings[0][0])
    for (x,y) in [point]:
        #x = np.random.randint(0, 127)
        #y = np.random.randint(0, 127)
        #print(x, y, matchings[1][b, y, x, 0], matchings[1][b, y, x, 1])
        if not np.isnan(matchings[img2][img1%N - (1 if img1 > img2 else 0), y, x, 0]).any():
            plt.plot([x, matchings[img2][img1%N - (1 if img1 > img2 else 0), y, x, 0] + 128], [y, matchings[img2][img1%N - (1 if img1 > img2 else 0), y, x, 1]], 'r-')

    plt.imshow(np.concatenate((images[img1], images[img2]), 1))
    plt.draw()


def onclick(event):
    if event.button == 2:
        point[0] = int(event.xdata)
        point[1] = int(event.ydata)
        print(point)
    draw()


fig,ax=plt.subplots()
fig.canvas.mpl_connect('button_press_event',onclick)
draw()
plt.show()
