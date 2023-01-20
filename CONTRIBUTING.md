# Contributing to BlenderProc

Thank you for your interest in BlenderProc.

The following is a short set of guidelines for contributing to BlenderProc. These are guidelines, not rules. If you feel like this set can be improved, feel free to propose changes in a PR.

## Contents

[Getting started](#getting-started)
 * [BlenderProc Source Code](#blenderproc-source-code)
 * [BlenderProc Design Decisions](#blenderproc-design-decisions)

[Ways to contribute](#ways-to-contribute)
 * [Reporting bugs](#reporting-bugs)
 * [Suggesting enchancements](#suggesting-enchancements)
 * [Pull Requests](#pull-requests)

[Styleguides](#styleguides)
 * [Git Commit Message and Branch Names](#git-commit-message-and-branch-names)
 * [Python Styleguide](#python-styleguide)
 * [BlenderProc Module Documentation Styleguide](#blenderproc-module-documentation-styleguide)
 * [BlenderProc Example Styleguide](#blenderproc-example-styleguide)

## Getting started

### BlenderProc Source Code

BlenderProc is a small open source project: just one repository. So when you decide to contribute to our ongoing effort to improve this tool, it is expected that you are familiar with the [source code](blenderproc/) and made your way through the relevant [examples](examples/).

### BlenderProc Design Decisions

At this point BlenderProc has a well-established project-wide code structure with key elements like modules, composite-modules, providers, utilities, examples, configuration files, etc. with the intent of keeping BlenderProc easy as an to use and easy to extend pipeline tool. The way the majority of this elements are developed is goverened by the [styleguides](#styleguides). But yes, it may happen such that the current way of organizing and developing is not suitable for your case, so use your best judgement.

## Ways to contribute

### Reporting bugs

Bugs are tracked as [GitHub issues](https://guides.github.com/features/issues/).
Create an issue, explain the problem and include additional details to help maintainers reproduce the problem:
* Use a clear and descriptive title.
* Describe the exact steps which reproduce the problem in as many details as possible.
* Provide specific examples to demonstrate the steps: part of the config file, copy/pasteable code snippets, etc.
* Explain which behavior you expected to see instead and why.
* Include screenshots if possible.

### Suggesting enchancements

Enhancement suggestions are tracked as [GitHub issues](https://guides.github.com/features/issues/).
Create an issue and provide the following information:
* Use a clear and descriptive title.
* Provide specific examples to demonstrate the steps: part of the config file, copy/pasteable code snippets, etc.
* Describe the current behavior and explain which behavior the enchancement will introduce.
* Explain why this enhancement would be useful.

### Pull Requests

In order to increase a pace of project-wide decision-making and maintain of the BlenderProc, please follow these steps to have your contribution considered by the maintainers:
* Link to the issue that your change relates to. If there is not yet an issue for your bug or issue for an enchancement request, please open a new issue and then link to that issue in your pull request.
* Fix description: short walk-through the concept of the solution.

If it is a bug fix PR:
* Verify that examples that use the fixed modules are working and their READMEs are updated if that is needed.

If it is an enchancement/feature PR:
* Provide a new example if major feature or enchancement is introduced.

The contents of the PR (i.e. code, documentation, examples) must follow the [styleguides](#styleguides).
While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.

## Styleguides

### Git Commit Message and Branch Names

Following is a simple pattern for Git Commit messages:

```
<type>(<scope>): <subject> 

<body>

<footer>
```
* `type` - type of the change, lowercase.

| type | meaning |
| ------ | ------- |
| `doc` | changes to the external or internal documentation|
| `feat` | new, removed or changed feature |
| `fix` | bug fix |
| `refactor` | refactoring/restructuring of the code |
| `revert` | reverted commit or parts of it |
| `style` | code cosmetica: formatting with no code change |
| `chore` | updating grunt tasks/maintaining with no production code change, cleanup |

* `subject` - the headline of the change, all lowercase.
* `scope` - scope of the change, all lowercase.
* `body` - optional text that describes your commit.
* `footer` - optional referencing of the issues, also all lowercase.

that may look like this:

```
feat(loader): add wavefront object loader

New module allows loading .obj files and setting custom properties like `physics` to the loaded objects.

closes #123
```

For branch names please stick to the issue number pattern of:

```
iss_300_some_short_name
```

### Python styleguide

We are trying to write good python code, but we are not hardcore Python evangelists. So use your best judgement, but remember that [PEP8](https://www.python.org/dev/peps/pep-0008/) dictates how to do things in general.

### BlenderProc Module Documentation Styleguide

We are using [Sphinx](https://www.sphinx-doc.org/en/master/index.html) for automatic generation of the API's documentation.
This way you are required to apply the following patterns:

* Pipeline Module Description

Depending on the amount of the parameters required/available to configure your module, and on the way they are required to be organized in the config file, provide list tables with parameter description/explanation along with general module description.
After the general description, please give a couple of examples with short explanation, try to show off all config parameters in them. For every parameter give a short explanation of its type, its default value, its range or available values, if applicable. The exact order is represented below.

```python
class MyNewPipelineModule(Loader):
    """ 
    This module is doing this, this, and this, while incorporating that.

    Example 1: Explain what happens

    .. code-block:: yaml

        {
          "some": "config",
          "example": "here"
        }

    Example 2: Explain this more complex example

    .. code-block:: yaml

        {
          "some": "more",
          "complex": "example"
        }

    **Table for a part of config**:
    
    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1
        
        * - Parameter
          - Description
          - Type
        * - param_a
          - Used for this/means this. Default: value. Available: [some_value, value, another_value].
          - type          
        * - param_b
          - Used for this/means this. Default: B. Range: [min, max]. 
          - type
                 
     **Table for another part of config if needed**:

     .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1
        
        * - Parameter
          - Description
          - Type
        * - param_c
          - Used for this. Contains that.
          - type          
        * - param_c/param_d
          - Used for this/means this.
          - type   
        * - param_c/param_e
          - Used for that/means that. Default: value. Available: [value, value1, value2].
          - type          
    """
```

* Pipeline Module Method Description

This one is pretty self-explanatory.

```python
def run(self):
    """ Doing this big thing in the following steps:
        1. Step 1
        2. Step 2
        ...
        N. Profit!!!
    """
    pass

def _foo(self, bar_a, bar_b):
    """ Sums bar_a and bar_b together and returns the result.
    
    :param a: Used for this/means this. Type: type.
    :param b: used for that/means that. Type: type.
    :return: A sum of bar_a and bar_b.
    """
    return bar_a + bar_b
```

### BlenderProc Example Styleguide

When you are proposing a new module or significant changes to the existing modules, new example as a part of your PR may be expected.
To create a good example, please follow these steps:
* Create a folder with a clear descriptive name in [examples](examples/) folder.
* In this folder provide at least a configuration config.yaml file and a README.md file.
* And any other files that may be necessary (like rendering images, .obj files, text files with some data required by the pipeline, etc), but keep it as clean as possible and **do not include any copyrighted materials**.

For the README.md of the example, please follow the [template](examples/EXAMPLE_README_TEMPLATE.md). If the proposed changes are not including some new modules or substantial changes in the existing ones, but an example is still required, then follow your best judgement.

Also remember, that when making changes to the existing modules it is up to you to verify that existing examples that are using this module are valid and working. Fix the configuration files and update READMEs of these examples, if the example requires it.
