FROM continuumio/miniconda3


ENTRYPOINT [ "/bin/bash", "-c" ]

ADD . /synther
WORKDIR /synther

#RUN \
#  conda update -n base conda -c anaconda && \
#  conda info && \
#  apt-get update && \
#  apt-get install -y libpq-dev build-essential && \
#  rm -rf /var/lib/apt/lists/*

#RUN conda env create && conda env list && activate synther && echo "CURRENT ENV: $CONDA_PREFIX"
RUN ./image.sh

# Hack to make activate work
#ENV PATH /opt/conda/envs/synther/bin:$PATH

#RUN \
#  conda env create -f environment.yml && \
#  conda activate synther

CMD [ "source activate synther && conda-build . --output-folder /build" ]
#CMD [ "source activate synther && conda-build . --output-folder /build" ]