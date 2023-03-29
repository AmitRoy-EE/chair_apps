# app/Dockerfile

# FROM continuumio/miniconda3:latest
# FROM python:3.9-slim
from mambaorg/micromamba:1.4-kinetic
# FROM mambaorg/micromamba:1.3.1

RUN mkdir chair_apps
WORKDIR /chair_apps
# copy repo contents to workdir
COPY . .
USER root
RUN chown -R $MAMBA_USER:$MAMBA_USER /chair_apps
USER $MAMBA_USER
# checkout everything from submodules
# RUN git submodule update --init -f --recursive 

# disable questions during installation
# ENV DEBIAN_FRONTEND noninteractive


RUN micromamba install -f env.yaml && \
    micromamba clean --all --yes



EXPOSE 8501

# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)
RUN pip install "protobuf~=3.19.0"

RUN python -c "import streamlit"

# first element is micromamba specific. For details see https://github.com/mamba-org/micromamba-docker 
# rest is taken from https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "streamlit", "run", "Home.py"]

# run with docker run -p 8501:8501 IMAGE_NAME