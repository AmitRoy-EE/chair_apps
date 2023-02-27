# app/Dockerfile

# FROM condaforge/mambaforge:latest

FROM mambaorg/micromamba:1.3.1

RUN mkdir chair_apps
WORKDIR /chair_apps
# copy repo contents to workdir
COPY --chown=$MAMBA_USER:$MAMBA_USER ./ /chair_apps

# disable questions during installation
# ENV DEBIAN_FRONTEND noninteractive

# RUN apt update && apt install -y \
#     build-essential \
#     curl \
#     software-properties-common \
#     git \
#     && rm -rf /var/lib/apt/lists/*

# RUN git clone https://gitlab.ruhr-uni-bochum.de/huckedyp/chair_apps.git .
# RUN pip3 install -r requirements.txt


RUN micromamba install -n base -f env.yaml && \
    micromamba clean --all --yes

EXPOSE 8501

# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# first element is micromamba specific. For details see https://github.com/mamba-org/micromamba-docker 
# rest is taken from https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]

# run with docker run -p 8501:8501 IMAGE_NAME