FROM mambaorg/micromamba:1.0.0
WORKDIR /usr/src/app
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1
ENV LD_LIBRARY_PATH=/opt/conda/lib:$LD_LIBRARY_PATH

COPY . .
