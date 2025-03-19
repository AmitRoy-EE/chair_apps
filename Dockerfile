
FROM mambaorg/micromamba:1.4-kinetic

RUN mkdir chair_apps
WORKDIR /chair_apps

# copy repo contents to workdir
COPY . .
USER root
RUN chown -R $MAMBA_USER:$MAMBA_USER /chair_apps
USER $MAMBA_USER

# replace whatever environment name with "base", which is required by the image
RUN  sed -i 's/name: \b[[:alpha:]]*\b/name: base/' env.yaml


RUN micromamba install -f env.yaml && \
    micromamba clean --all --yes



EXPOSE 8501

ARG MAMBA_DOCKERFILE_ACTIVATE=1  # (otherwise python will not be found)
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
RUN python -c "import streamlit"

# first element is micromamba specific. For details see https://github.com/mamba-org/micromamba-docker 
# rest is taken from https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "streamlit", "run", "Home.py"]

# run with docker run -p 8501:8501 IMAGE_NAME