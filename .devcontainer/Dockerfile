# Choices listed at https://github.com/devcontainers/images/blob/v0.3.10/src/python/.devcontainer/Dockerfile#L1
# Note: If on arm64/Apple Silicon, must use -bullseye variant.
ARG VARIANT="3.11-bookworm"
FROM mcr.microsoft.com/vscode/devcontainers/python:${VARIANT}

# Install dev dependencies globally in the image.
# (Still easy to experiment with upgrades/new dependencies by installing them in --user scope,
# and if you want to keep them, add them to the requirements file and rebuild the container.)
COPY dev-deps/python3.11/*.txt /tmp/bidict-dev-deps/
RUN pip3 --disable-pip-version-check install -U pip && \
  pip3 --disable-pip-version-check --no-cache-dir install \
  -r /tmp/bidict-dev-deps/test.txt \
  -r /tmp/bidict-dev-deps/lint.txt \
  -r /tmp/bidict-dev-deps/docs.txt \
  -r /tmp/bidict-dev-deps/dev.txt \
  && rm -rf /tmp/bidict-dev-deps

# [Optional] Install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends \
  graphviz optipng  `# for docs/_static/build-bidict-types-diagram.sh` \
  fish              `# make fish shell available for development`
