# What is Synther? [Currently in development]

Synther is a python library that enables a theory-oriented programmatic approach to making music that is more typically produced with Digital Audio Workstation (DAW) software tools.

## To Install latest build...

```bash
conda install -c ptrick synther
```

## Features

### Build system

Render output files only when you need to. The synther build system will track changes to any part of the music production process enabling speedy iterative development.

### Theory-based

No user-interface fluff. Produce music with intention, science, math, and theory.

### Modular

This tool works best when it's out of your way. We do the heavy lifting (low-level wave generation, extraction, transformation, and loading) in a C library, and then wrap it minimally with a python module and the build system. Additional python modules can easily interact with it by queueing parameterized/customized commands in the build system, enabling rapid development of modules.

## Examples

Go to the [Example repository](https://github.com/ptrick/synther-examples.git).

## Getting Started with Modifications (Simple Edition)

If you're just looking to mess around in a more relaxed environment, conda is not necessary for this particular package. A normal installation of [Python 3](https://www.python.org/) will do just fine.

You can start making modifications in `/src` right away. Then, to install in your python package cache, use:

```bash
pip install .
```

To start using the package, add this to the top of any python file...

```python
import synther
```

Happy hacking!

## Making Modifications (Conda)

### Prerequisites:

* Conda. To do this, it is recommended to install: [Anaconda](https://www.anaconda.com/)

### Step 1 - Set up the Environment

```bash
conda env create -f environment.yml
```

### Step 2 - Make your modifications

Modify the files to your liking in the `src/` directory.

### Step 3 - Build the conda package
```bash
conda-build . --output-folder build
```

The `--output-folder build` part of that will dump the files to the build folder in the working directory.

### Step 4 - Upload packages to wherever you need it

The easiest method would be to follow the directions for uploading a package to the [Anaconda Cloud](https://docs.anaconda.com/anaconda-cloud/user-guide/tasks/work-with-packages/#uploading-packages).

Another option would be to use your local filesystem as a conda channel host. Refer to [this documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/create-custom-channels.html) for more information.

### Step 5 - Consume!

```bash
conda activate <SOME_OTHER_ENVIRONMENT>
conda install -c <YOUR_CUSTOM_CHANNEL> synther
```

And then in some python file:
```python
import synther
```
Happy hacking!