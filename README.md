# What is Synther? [Currently in development]

Synther is a python library that enables a theory-oriented programmatic approach to making music that is more typically produced with Digital Audio Workstation (DAW) software tools.

## Features

### Build system

Render output files only when you need to. The synther build system will track changes to any part of the music production process enabling speedy iterative development.

### Theory-based

No user-interface fluff. Produce music with intention, science, math, and no limitations as far as the sound is concerned. We sacrifice any live features, as this works best as a step in the music refinement pipeline.

### Modular

This tool works best when it's out of your way. We do the heavy lifting (low-level wave generation, extraction, transformation, and loading) in a C library, and then wrap it minimally with a python module and the build system. Additional python modules can easily interact with it by queueing parameterized/customized commands in the build system, enabling rapid development of modules.

### Scientific Journals for Music Arrangements

It doesn't have to be only about the end result; how you get there can be equally interesting! The examples in \notebooks\ are written with Jupyter notebooks to encourage a fun process of sharing and discovery! Markdown is combined with Python code in a contiguous document written in a journal-like manner. And discovery is really what synther is all about.

## Layout

```
|
|
|__> \data\ <-- miscellaneous data used to inform production
|__> \midi\ <-- midi files used in notebooks
|__> \modules\ <-- custom modules that extend the functionality of synther
|__> \notebooks\ <-- tutorials and documented example musical arrangements
|__> \samples\ <-- sounds used in notebooks
|__> \synther\ <-- The core of synther C lib and the build system
```

## Installation requirements

You may need:

* [Python 3](https://www.python.org/downloads/) (Tested on 3.6.2)
* [Jupyter Notebooks](https://jupyter.org/)

For some of the examples, we rely on:

```bash
pip install playsound
pip install numpy
pip install matplotlib
```

## Running an example notebook

```bash
git clone https://github.com/ptrick/synther.git

cd synther

pip install ./synther
pip install ./modules

cd notebooks
jupyter notebook
```