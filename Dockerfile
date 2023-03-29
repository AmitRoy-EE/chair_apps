# app/Dockerfile

# FROM continuumio/miniconda3:latest
FROM condaforge/mambaforge:latest

# FROM mambaorg/micromamba:1.3.1

# RUN mkdir chair_apps
# WORKDIR /chair_apps
# copy repo contents to workdir
COPY . .


# checkout everything from submodules
# RUN git submodule update --init -f --recursive 

# disable questions during installation
ENV DEBIAN_FRONTEND noninteractive


RUN mamba env update -f env.yaml && \
    mamba clean --all --yes

EXPOSE 8501

# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# first element is micromamba specific. For details see https://github.com/mamba-org/micromamba-docker 
# rest is taken from https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker
ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]

# run with docker run -p 8501:8501 IMAGE_NAME