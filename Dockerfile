FROM alpine:3.19 AS get-pandoc
WORKDIR /tmp/pandoc
RUN arch=$(arch | sed s:aarch64:arm64: | sed s:x86_64:amd64:) \
    && wget https://github.com/jgm/pandoc/releases/download/2.19/pandoc-2.19-linux-$arch.tar.gz -O- | tar -xz --strip-components=1

FROM python:3.11-alpine3.19 AS build-package
COPY setup.py .
COPY src src
RUN python setup.py sdist

FROM python:3.11-alpine3.19 AS install-dependencies
COPY --from=build-package /sobiraka.egg-info/requires.txt .
RUN pip install --prefix /prefix --requirement requires.txt

FROM python:3.11-alpine3.19 AS install-dependencies-tester
RUN pip install --prefix /prefix coverage~=7.0.0

FROM python:3.11-alpine3.19 AS install-dependencies-linter
RUN pip install --prefix /prefix pylint~=2.17.4

FROM install-dependencies AS install-package
COPY --from=build-package /dist/*.tar.gz .
RUN pip install --prefix /prefix *.tar.gz

FROM python:3.11-alpine3.19 AS common-html
RUN apk add --no-cache hunspell
COPY --from=get-pandoc /tmp/pandoc /usr/local
WORKDIR /W
ENTRYPOINT [""]

FROM python:3.11-alpine3.19 AS common
RUN apk add --no-cache texlive-full
RUN apk add --no-cache hunspell
COPY --from=get-pandoc /tmp/pandoc /usr/local
WORKDIR /W
ENTRYPOINT [""]

FROM common AS tester-src
RUN apk add --no-cache git make poppler-utils
ARG UID=1000
ARG GID=1000
RUN addgroup mygroup -g $GID
RUN adduser myuser -u $UID -G mygroup -D
USER myuser
ENV PATH=/home/myuser/.local/bin:$PATH
COPY --from=install-dependencies /prefix /usr/local
COPY --from=install-dependencies-tester /prefix /usr/local
CMD make tests

FROM tester-src AS tester-dist
COPY --from=install-package /prefix /usr/local
COPY Makefile .
COPY tests tests
CMD make tests

FROM tester-src AS linter
COPY --from=install-dependencies-linter /prefix /usr/local
CMD make lint

FROM common-html AS release-html
COPY --from=install-package /prefix /usr/local

FROM common AS release
COPY --from=install-package /prefix /usr/local