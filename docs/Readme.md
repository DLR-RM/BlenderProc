# Documentation


The scripts assume that blender is installed at `/home_local/${USER}/blender/blender-2.92.0-linux64`.
If this is not the case please change it in the [Makefile](Makefile).

First run `config_for_pip_install.yaml` to make sure to install all packages used in our code:

```bash
python cli.py docs/config_for_pip_install.yaml
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
