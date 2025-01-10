ARG PANDOC
ARG PYTHON

ARG NODE=20.17
ARG PYTHON_FOR_BUILDING=3.13


################################################################################
# Install dependencies

FROM python:$PYTHON_FOR_BUILDING AS build-package
RUN --mount=type=cache,target=/root/.cache/pip pip install setuptools
COPY setup.py .
COPY src src
RUN python setup.py sdist

FROM python:$PYTHON_FOR_BUILDING AS get-tester-dependencies
RUN apt update
RUN apt install --yes --download-only git poppler-utils

FROM python:$PYTHON AS get-deb-packages
RUN apt update
RUN apt install --yes --download-only weasyprint hunspell

FROM python:$PYTHON_FOR_BUILDING AS get-conda
RUN wget --progress=bar:force https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
RUN chmod +x /tmp/miniconda.sh

FROM python:$PYTHON_FOR_BUILDING AS get-fonts
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
# Install dependencies that we could not install before python-nodejs

FROM python-nodejs AS install-pip-dependencies
COPY --from=build-package /sobiraka.egg-info/requires.txt .
RUN pip install --prefix /prefix --requirement requires.txt

FROM python-nodejs AS install-pip-dependencies-for-tester
RUN pip install --prefix /prefix coverage~=7.0.0

FROM install-pip-dependencies AS install-package
COPY --from=build-package /dist/*.tar.gz .
RUN pip install --prefix /prefix *.tar.gz


################################################################################
# The base image for all final images

FROM latex-python-nodejs AS common-latex
COPY --from=get-deb-packages /var/cache/apt /var/cache/apt
RUN apt install --yes weasyprint hunspell
RUN --mount=type=cache,target=/root/.npm npm install -g pagefind sass
COPY --from=get-fonts /tmp/fonts /usr/share/fonts
ENTRYPOINT [""]

FROM python-nodejs AS common
COPY --from=get-deb-packages /var/cache/apt /var/cache/apt
RUN apt install --yes weasyprint hunspell
RUN --mount=type=cache,target=/root/.npm npm install -g pagefind sass
COPY --from=get-fonts /tmp/fonts /usr/share/fonts
ENTRYPOINT [""]


################################################################################
# Final images

FROM common-latex AS tester
RUN apt install --yes git poppler-utils
COPY --from=get-tester-dependencies /var/cache/apt /var/cache/apt
COPY --from=install-pip-dependencies-for-tester /prefix /opt/conda/envs/myenv
COPY --from=install-pip-dependencies /prefix /opt/conda/envs/myenv
COPY --from=install-package /prefix /opt/conda/envs/myenv
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
COPY --from=install-pip-dependencies /prefix /opt/conda/envs/myenv
COPY --from=install-package /prefix /opt/conda/envs/myenv
CMD sobiraka

FROM common AS release
COPY --from=install-pip-dependencies /prefix /opt/conda/envs/myenv
COPY --from=install-package /prefix /opt/conda/envs/myenv
CMD sobiraka