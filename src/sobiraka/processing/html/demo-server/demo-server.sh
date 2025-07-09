#!/usr/bin/env sh

export SERVER=$(dirname $0)
export THEME=$1
export PAGEFIND=$(realpath $(dirname $0)/../../../../../docs/build/_pagefind)

cd $THEME
sass sass/web.scss _static/theme.css --load-path=$SERVER/sass --watch &
caddy run --config $SERVER/Caddyfile