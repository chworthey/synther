[![Build Status](https://dev.azure.com/pworthey007/Synther/_apis/build/status/ptrick.synther?branchName=master)](https://dev.azure.com/pworthey007/Synther/_build/latest?definitionId=5&branchName=master)

# What is Synther? [Currently in development]

Synther is a python library that enables a theory-oriented programmatic approach to making music that is more typically produced with Digital Audio Workstation (DAW) software tools.

## To Install latest build for your project...

```bash
conda activate <YOUR ENVIRONMENT>
conda install -c ptrick synther
```

## Documentation

### Examples

Check out the [Examples repository](https://github.com/ptrick/synther-examples.git). Interactive Binders are available there.

### References

Check out the [docs](https://ptrick.github.io/synther-ref/).

## Synther Features

### Build system

Render output files only when you need to. The synther build system will track changes to any part of the music production process enabling speedy iterative development.

### Theory-based

No user-interface fluff. Produce music with intention, science, math, and theory.

### Modular

This tool works best when it's out of your way. We do the heavy lifting in a C library, and then wrap it minimally with a python module and the build system. Additional python modules can easily interact with it by queueing parameterized/customized commands in the build system, enabling rapid development of modules.

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

## Making Modifications (Conda, local machine)

### Prerequisites:

* Conda. To do this, it is recommended to install: [Anaconda](https://www.anaconda.com/). [Miniconda](https://docs.conda.io/en/latest/miniconda.html) will also work.

### Step 1 - Set up the Environment

```bash
conda env create -f environment.yml
```

### Step 2 - Make your modifications

Modify the files to your liking in the `src/` directory.

### Step 3 - Activate environment

```bash
conda activate synther
```

### Step 4 - Build the conda package
```bash
conda-build . --output-folder build
```

The `--output-folder build` part of that will dump the files to the build folder in the working directory.

### Step 5 - Upload packages to wherever you need it

The easiest method would be to follow the directions for uploading a package to the [Anaconda Cloud](https://docs.anaconda.com/anaconda-cloud/user-guide/tasks/work-with-packages/#uploading-packages).

Another option would be to use your local filesystem as a conda channel host. Refer to [this documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/create-custom-channels.html) for more information.

### Step 6 - Consume!

```bash
conda activate <SOME_OTHER_ENVIRONMENT>
conda install -c <YOUR_CUSTOM_CHANNEL> synther
```

And then in some python file:
```python
import synther
```
Happy hacking!

## Sandboxing

To get the build environment more stable, use the steps outlined below for using the docker integration.

### Prerequisites:

* [Docker](https://www.docker.com/products/docker-desktop)

Docker needs to be configured to the linux environment.

### Step 1 - Build the image

```bash
docker build -t synther .
```

### Step 2 - Do something with it

```bash
docker run -it synther "<YOUR_COMMAND_HERE>"
```