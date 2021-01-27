from pathlib import Path
import shutil

output = Path(__file__).absolute().parent / "source" / "examples"
if output.exists():
    shutil.rmtree(str(output))
output.mkdir()

examples = (Path(__file__).absolute().parent.parent / "examples")

for example in examples.rglob("**/README.md"):
    output_example = Path(str(example).replace(str(examples), str(output))).parent
    output_example.mkdir(exist_ok=True, parents=True)

    shutil.copy(str(example), str(output_example / "README.md"))

shutil.copy(examples.parent / "BlenderProcVideoImg.jpg", output.parent)
shutil.copy(examples.parent / "readme.jpg", output.parent)
shutil.copy(examples.parent / "README.md", output.parent)
shutil.copy(examples.parent / "change_log.md", output.parent)
shutil.copy(examples.parent / "CONTRIBUTING.md", output.parent)

for ext in ["**/*.jpg", "**/*.png"]:
    for example in examples.rglob(ext):
        output_example = Path(str(example).replace(str(examples), str(output)))
        output_example.parent.mkdir(exist_ok=True, parents=True)

        shutil.copy(str(example), str(output_example))