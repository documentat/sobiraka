FROM alpine:3.16 AS get-pandoc
WORKDIR /tmp/pandoc
RUN arch=$(arch | sed s:aarch64:arm64: | sed s:x86_64:amd64:) \
    && wget https://github.com/jgm/pandoc/releases/download/2.18/pandoc-2.18-linux-$arch.tar.gz -O- | tar -xz --strip-components=1

FROM alpine:3.16 AS get-fonts
RUN wget http://rus.paratype.ru/system/attachments/631/original/ptmono.zip -O ptmono.zip && unzip ptmono.zip -d /tmp/fonts && rm ptmono.zip
RUN wget https://www.latofonts.com/download/lato2ofl-zip/ -O lato.zip && unzip lato.zip -d /tmp/fonts && rm lato.zip

FROM python:3.11-alpine3.16 AS build-package
COPY setup.py .
COPY src src
RUN python setup.py sdist

FROM python:3.11-alpine3.16 AS install-dependencies
RUN ln -s /usr/local/bin/python /usr/bin/python
COPY --from=build-package /sobiraka.egg-info/requires.txt .
RUN /usr/bin/python -m pip install --prefix /prefix --requirement requires.txt

FROM python:3.11-alpine3.16 AS install-dependencies-linter
RUN ln -s /usr/local/bin/python /usr/bin/python
RUN /usr/bin/python -m pip install --prefix /prefix pylint~=2.17.4

FROM install-dependencies AS install-package
COPY --from=build-package /dist/*.tar.gz .
RUN /usr/bin/python -m pip install --prefix /prefix *.tar.gz

FROM pandoc/latex:2.19 AS common
RUN chmod 777 /var/cache/fontconfig
RUN apk add --no-cache python3~=3.11 --repository=http://dl-cdn.alpinelinux.org/alpine/edge/main/
RUN apk add hunspell
RUN tlmgr install koma-script ragged2e enumitem
COPY --from=get-pandoc /tmp/pandoc /usr/local
COPY --from=get-fonts /tmp/fonts /usr/share/fonts/truetype
WORKDIR /W
ENTRYPOINT [""]

FROM common AS tester-src
RUN apk add git make poppler-utils
RUN apk add --no-cache py3-pip --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community/
RUN pip install --break-system-packages coverage~=7.0.0
ARG UID=1000
ARG GID=1000
RUN addgroup mygroup -g $GID
RUN adduser myuser -u $UID -G mygroup -D
USER myuser
ENV PATH=/home/myuser/.local/bin:$PATH
COPY --from=install-dependencies /prefix /usr
CMD make tests

FROM tester-src AS tester-dist
COPY --from=install-package /prefix /usr
COPY Makefile .
COPY tests tests
CMD make tests

FROM tester-src AS linter
COPY --from=install-dependencies-linter /prefix /usr
CMD make lint

FROM common AS release
COPY --from=install-package /prefix /usr
