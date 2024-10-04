ARG PANDOC
ARG PYTHON

ARG NODE=20.17
ARG UBUNTU=24.10


################################################################################
# Install dependencies

FROM python:$PYTHON AS build-package
RUN --mount=type=cache,target=/root/.cache/pip pip install setuptools
COPY setup.py .
COPY src src
RUN python setup.py sdist

FROM python:$PYTHON AS get-tester-dependencies
RUN apt update
RUN apt install --yes --download-only git poppler-utils

FROM python:$PYTHON AS get-weasyprint
RUN apt update
RUN apt install --yes --download-only weasyprint

FROM python:$PYTHON AS get-conda
RUN wget --progress=bar:force https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
RUN chmod +x /tmp/miniconda.sh

FROM python:$PYTHON AS get-fonts
RUN wget --progress=bar:force https://www.latofonts.com/download/lato2ofl-zip/ -O lato.zip
RUN unzip lato.zip **/*.ttf -d /tmp/fonts
RUN wget --progress=bar:force https://download.jetbrains.com/fonts/JetBrainsMono-2.304.zip -O jbmono.zip
RUN unzip jbmono.zip **/*.ttf -d /tmp/fonts


################################################################################
# Base images

FROM pandoc/latex:$PANDOC-ubuntu AS latex-python-nodejs
WORKDIR /W
RUN tlmgr install koma-script
RUN apt update
COPY --from=get-conda /tmp/miniconda.sh /tmp/miniconda.sh
RUN /tmp/miniconda.sh -b -m -p /opt/conda && rm /tmp/miniconda.sh
ENV PATH /opt/conda/bin:$PATH
ARG NODE
ARG PYTHON
RUN conda create -y --name myenv python=$PYTHON nodejs=$NODE
ENV PATH /opt/conda/envs/myenv/bin:$PATH

FROM pandoc/core:$PANDOC-ubuntu AS python-nodejs
WORKDIR /W
RUN apt update
COPY --from=get-conda /tmp/miniconda.sh /tmp/miniconda.sh
RUN /tmp/miniconda.sh -b -m -p /opt/conda && rm /tmp/miniconda.sh
ENV PATH /opt/conda/bin:$PATH
ARG NODE
ARG PYTHON
RUN conda create -y --name myenv python=$PYTHON nodejs=$NODE
ENV PATH /opt/conda/envs/myenv/bin:$PATH


################################################################################
# The base image for all final images

FROM latex-python-nodejs AS common-latex
COPY --from=get-weasyprint /var/cache/apt /var/cache/apt
RUN apt install --yes weasyprint
RUN --mount=type=cache,target=/root/.npm npm install -g pagefind
COPY --from=get-fonts /tmp/fonts /usr/share/fonts
ENTRYPOINT [""]

FROM python-nodejs AS common
COPY --from=get-weasyprint /var/cache/apt /var/cache/apt
RUN apt install --yes weasyprint
RUN --mount=type=cache,target=/root/.npm npm install -g pagefind
COPY --from=get-fonts /tmp/fonts /usr/share/fonts
ENTRYPOINT [""]


################################################################################
# Final images

FROM common-latex AS tester
COPY --from=get-tester-dependencies /var/cache/apt /var/cache/apt
RUN apt install --yes git poppler-utils
RUN --mount=type=cache,target=/root/.cache/pip pip install coverage~=7.0.0
COPY --from=build-package /dist/*.tar.gz .
RUN --mount=type=cache,target=/root/.cache/pip pip install *.tar.gz && rm *.tar.gz
ARG UID=1000
ARG GID=1000
RUN addgroup --gid $GID myuser || true
RUN adduser --uid $UID --gid $GID myuser || true
USER 1000
COPY tests .
ENV COVERAGE_FILE /tmp/coverage
CMD python -m coverage run --source=sobiraka -m unittest discover --start-directory=. --verbose \
	&& python -m coverage report --precision=1 --skip-empty --skip-covered --show-missing

FROM common-latex AS release-latex
COPY --from=build-package /dist/*.tar.gz .
RUN --mount=type=cache,target=/root/.cache/pip pip install *.tar.gz && rm *.tar.gz
CMD sobiraka

FROM common AS release
COPY --from=build-package /dist/*.tar.gz .
RUN --mount=type=cache,target=/root/.cache/pip pip install *.tar.gz && rm *.tar.gz
CMD sobiraka