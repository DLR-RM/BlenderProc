from pathlib import Path
import shutil


def repair_anchors(file):
    with open(file) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        if lines[i].startswith("##"):
            lines.insert(i, ".. _" + "_".join(lines[i].split()[1:]).lower() + ":\n")
            i += 1
        i += 1

    with open(file, "w") as f:
        f.write("\n".join(lines))

output = Path(__file__).absolute().parent / "source" / "examples"
if output.exists():
    shutil.rmtree(str(output))
output.mkdir()

examples = (Path(__file__).absolute().parent.parent / "examples")

for example in examples.rglob("**/README.md"):
    output_example = Path(str(example).replace(str(examples), str(output))).parent
    output_example.mkdir(exist_ok=True, parents=True)

    shutil.copy(str(example), str(output_example / "README.md"))

if (output.parent / "images").exists():
    shutil.rmtree(output.parent / "images")
shutil.copytree(examples.parent / "images", output.parent / "images")
shutil.copy(examples.parent / "README.md", output.parent)
repair_anchors(output.parent / "README.md")
shutil.copy(examples.parent / "README_BlenderProc4BOP.md", output.parent)
shutil.copy(examples.parent / "change_log.md", output.parent)
shutil.copy(examples.parent / "CONTRIBUTING.md", output.parent)

if (output.parent / "docs" / "tutorials").exists():
    shutil.rmtree(output.parent / "docs" / "tutorials")
shutil.copytree(examples.parent / "docs" / "tutorials", output.parent / "docs" / "tutorials")

for ext in ["**/*.jpg", "**/*.png"]:
    for example in examples.rglob(ext):
        output_example = Path(str(example).replace(str(examples), str(output)))
        output_example.parent.mkdir(exist_ok=True, parents=True)

        shutil.copy(str(example), str(output_example))
