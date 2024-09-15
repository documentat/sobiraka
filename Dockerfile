################################################################################
# The base for most images

FROM python:3.11-alpine3.19 AS python-and-nodejs
RUN apk add --no-cache nodejs npm


################################################################################
# Install Python and NodeJS dependencies

# Build Sobiraka
FROM python:3.11-alpine3.19 AS build-package
COPY setup.py .
COPY src src
RUN python setup.py sdist

FROM python:3.11-alpine3.19 AS install-pip-dependencies
COPY --from=build-package /sobiraka.egg-info/requires.txt .
RUN pip install --prefix /prefix --requirement requires.txt

FROM python:3.11-alpine3.19 AS install-pip-dependencies-for-tester
RUN pip install --prefix /prefix coverage~=7.0.0

FROM python:3.11-alpine3.19 AS install-pip-dependencies-for-linter
RUN pip install --prefix /prefix pylint~=3.1.0

FROM python-and-nodejs AS install-npm-dependencies
WORKDIR /opt
ADD package.json .
RUN npm install --verbose


################################################################################
# Download additional utilities

FROM alpine:3.19 AS get-pandoc
WORKDIR /tmp/pandoc
RUN arch=$(arch | sed s:aarch64:arm64: | sed s:x86_64:amd64:) \
    && wget https://github.com/jgm/pandoc/releases/download/3.2.1/pandoc-3.2.1-linux-$arch.tar.gz -O-  \
    | tar -xz --strip-components=1


################################################################################
# Download fonts

FROM alpine:3.19 AS get-fonts
WORKDIR /tmp/fonts
RUN wget https://www.latofonts.com/download/lato2ofl-zip/ -O /tmp/lato.zip && unzip /tmp/lato.zip && rm /tmp/lato.zip
RUN mv Lato2OFL/*.ttf .
RUN wget https://download.jetbrains.com/fonts/JetBrainsMono-2.304.zip -O /tmp/jbmono.zip && unzip /tmp/jbmono.zip && rm /tmp/jbmono.zip
RUN mv fonts/ttf/*.ttf .


################################################################################
# Install Sobiraka

FROM install-pip-dependencies AS install-package
COPY --from=build-package /dist/*.tar.gz .
RUN pip install --prefix /prefix *.tar.gz


################################################################################
# The base images for all final images

FROM python-and-nodejs AS common-html
RUN apk add --no-cache hunspell
RUN apk add --no-cache weasyprint
COPY --from=install-npm-dependencies /opt/node_modules /node_modules
COPY --from=get-pandoc /tmp/pandoc /usr/local
COPY --from=get-fonts /tmp/fonts /usr/share/fonts
WORKDIR /W
ENTRYPOINT [""]

FROM python-and-nodejs AS common
RUN apk add --no-cache texlive-full
RUN apk add --no-cache hunspell
RUN apk add --no-cache weasyprint
COPY --from=install-npm-dependencies /opt/node_modules /node_modules
COPY --from=get-pandoc /tmp/pandoc /usr/local
COPY --from=get-fonts /tmp/fonts /usr/share/fonts
WORKDIR /W
ENTRYPOINT [""]


################################################################################
# Final images

FROM common AS tester-src
RUN apk add --no-cache git make poppler-utils
ARG UID=1000
ARG GID=1000
RUN addgroup mygroup -g $GID
RUN adduser myuser -u $UID -G mygroup -D
USER myuser
ENV PATH=/home/myuser/.local/bin:$PATH
COPY --from=install-pip-dependencies /prefix /usr/local
COPY --from=install-pip-dependencies-for-tester /prefix /usr/local
CMD make tests

FROM tester-src AS tester-dist
COPY --from=install-package /prefix /usr/local
COPY Makefile .
COPY tests tests
CMD make tests

FROM tester-src AS linter
COPY --from=install-pip-dependencies-for-linter /prefix /usr/local
CMD make lint

FROM common-html AS release-html
COPY --from=install-package /prefix /usr/local

FROM common AS release
COPY --from=install-package /prefix /usr/local