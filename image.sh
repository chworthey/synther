#!/bin/bash

conda update -n base -c defaults conda

conda env create -f environment.yml
source activate synther

conda-build . --output-folder /build