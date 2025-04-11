# Documentation


The scripts assume that blender is installed at `/home_local/$USER/blender/blender-3.3.1-linux-x64/blender`.
If this is not the case please change it in the [Makefile](Makefile).

First make sure to install all necessary packages:

```bash
blenderproc pip install sphinx pygments packaging sphinx-autodoc-typehints sphinx-autodoc-typehints m2r2 sphinx-rtd-theme docutils
```

```bash
blenderproc pip install git+https://github.com/abahnasy/smplx git+https://github.com/abahnasy/human_body_prior git+https://github.com/wboerdijk/urdfpy.git git+https://github.com/thodan/bop_toolkit PyOpenGL==3.1.0
```

Now copy markdowns files from examples and main directory:

```bash
cd docs
python prepare_markdown.py
```

You can regenerate the documentation by executing:

```bash
./generate.sh
```

The main index file will be at: BlenderProc/docs/build/html/index.html
