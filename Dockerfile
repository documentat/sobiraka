ARG PANDOC=3.7
ARG PYTHON=3.13

ARG ALPINE=3.21
ARG LATEX=2025.1
ARG NODE=20.18.1
ARG PYTHON_FOR_BUILDING=3.13


#region Install dependencies

FROM node:$NODE-alpine$ALPINE AS node

FROM python:$PYTHON-alpine$ALPINE AS python

FROM kjarosh/latex:$LATEX-small AS latex

FROM python:$PYTHON-alpine$ALPINE AS get-hatch
RUN python -m venv /HATCH
ENV PATH=/HATCH/bin:$PATH
RUN --mount=type=cache,target=/root/.cache/pip pip install build~=1.2

FROM python:$PYTHON-alpine$ALPINE AS get-pip-dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install build~=1.2 hatch~=1.4
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/pip hatch dep show requirements | xargs pip download --dest=/PIP

FROM python:$PYTHON_FOR_BUILDING-alpine$ALPINE AS build-package
RUN --mount=type=cache,target=/root/.cache/pip pip install build~=1.2 hatch~=1.4
COPY pyproject.toml .
COPY README.md .
COPY src src
RUN --mount=type=cache,target=/root/.cache/pip python -m build --verbose --outdir=/PIP

FROM alpine:$ALPINE AS get-pandoc
WORKDIR /opt/pandoc
ARG PANDOC
RUN wget https://github.com/jgm/pandoc/releases/download/$PANDOC/pandoc-$PANDOC-linux-amd64.tar.gz -O-  \
    | tar -xz --strip-components=1

FROM alpine:$ALPINE AS get-fonts
RUN wget https://www.latofonts.com/download/lato2ofl-zip/ -O lato.zip
RUN unzip lato.zip **/*.ttf -d /tmp/fonts
RUN wget https://download.jetbrains.com/fonts/JetBrainsMono-2.304.zip -O jbmono.zip
RUN unzip jbmono.zip **/*.ttf -d /tmp/fonts

FROM python:$PYTHON-alpine$ALPINE AS install-package
RUN --mount=type=cache,target=/root/.cache/pip pip install build~=1.2 hatch~=1.4
RUN hatch --version
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/pip hatch dep show requirements | xargs pip download --dest=/PIP
RUN hatch dep show requirements | xargs pip install --no-index --find-links=/PIP --prefix=/VENV
RUN mkdir -p /VENV/bin && cp /usr/local/bin/python /VENV/bin/python
COPY --from=build-package /PIP/sobiraka-*.tar.gz /PIP
RUN /VENV/bin/python -m pip install /PIP/sobiraka-* --no-index --find-links=/PIP --prefix=/VENV
RUN rm /VENV/bin/python

FROM python:$PYTHON-alpine$ALPINE AS install-pip-dependencies-for-linter
RUN pip install --prefix=/VENV pylint

FROM alpine:$ALPINE AS install-npm-dependencies
RUN --mount=type=cache,target=/var/cache/apk apk add nodejs npm
WORKDIR /NODE
ADD package.json .
ADD package-lock.json .
RUN --mount=type=cache,target=/root/.npm npm install --loglevel=verbose

# endregion

# region The base images for all final images

FROM python:$PYTHON-alpine$ALPINE AS base
WORKDIR /W
COPY --from=node / /
RUN python -m venv /VENV
ENV PATH=/VENV/bin:$PATH
COPY --from=get-pip-dependencies /PIP /PIP
RUN pip install /PIP/*
RUN --mount=type=cache,target=/var/cache/apk apk add hunspell
RUN --mount=type=cache,target=/var/cache/apk apk add py3-pip so:libgobject-2.0.so.0 so:libpango-1.0.so.0 so:libharfbuzz.so.0 so:libharfbuzz-subset.so.0 so:libfontconfig.so.1 so:libpangoft2-1.0.so.0
RUN --mount=type=cache,target=/var/cache/apk apk add gcc musl-dev python3-dev zlib-dev jpeg-dev openjpeg-dev libwebp-dev g++ libffi-dev
RUN pip install weasyprint
COPY --from=get-fonts /tmp/fonts /usr/share/fonts
COPY --from=get-pandoc /opt/pandoc /usr/local
COPY --from=install-npm-dependencies /NODE /NODE
ENV NODE_PATH=/NODE/node_modules
ENTRYPOINT [""]

FROM base AS base-latex
COPY --from=latex /opt/texlive /opt/texlive
ENV PATH=/opt/texlive/bin/x86_64-linuxmusl:$PATH

# endregion

# region Final images

FROM base AS release
COPY --from=build-package /PIP /PIP
RUN pip install /PIP/sobiraka*.whl
CMD ["sobiraka"]
ARG GITHUB_REF_NAME
ARG GITHUB_SHA
ARG CREATED
ARG VERSION
ARG PUBLIC_REPOSITORY_URL
ARG DOCS_MASTER_URL
LABEL maintainer="Max Alibaev <max.alibaev@documentat.io>"
LABEL org.opencontainers.image.title="Sobiraka"
LABEL org.opencontainers.image.description="HTML and PDF documentation builder"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="$VERSION"
LABEL org.opencontainers.image.created="$CREATED"
LABEL org.opencontainers.image.ref.name="$GITHUB_REF_NAME"
LABEL org.opencontainers.image.revision="$GITHUB_SHA"
LABEL org.opencontainers.image.source="$PUBLIC_REPOSITORY_URL"
LABEL org.opencontainers.image.url="$DOCS_MASTER_URL"

FROM release AS release-latex
COPY --from=latex /opt/texlive /opt/texlive
ENV PATH=/opt/texlive/bin/x86_64-linuxmusl:$PATH

FROM release-latex AS tester
RUN --mount=type=cache,target=/var/cache/apk apk add poppler-utils
#RUN --mount=type=cache,target=/root/.cache/pip pip install build~=1.2 hatch~=1.14
COPY --from=build-package /PIP /PIP
RUN pip install /PIP/sobiraka*.whl
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["python", "-m", "unittest", "discover", "--start-directory=tests", "--verbose"]

FROM tester AS linter
COPY --from=install-pip-dependencies-for-linter /VENV /VENV
ENV PYTHONPATH=src:tests
ENTRYPOINT [""]

# endregion