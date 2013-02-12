#!/bin/sh

if [ ! -f *.spec ]; then
    echo "Cannot find spec file"
    exit 2
fi

if [ -f ./get_sources.sh ]; then
    sh ./get_sources.sh
elif [ -x /usr/bin/spectool ]; then
    /usr/bin/spectool -g *.spec
else
    echo "Cannot download source"
    exit 1
fi
