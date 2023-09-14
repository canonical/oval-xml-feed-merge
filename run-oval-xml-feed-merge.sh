#!/bin/bash

# Based on https://forum.snapcraft.io/t/reliable-way-of-detecting-snap-confinement-mode/8896/5
CONFINEMENT=$(grep confinement $SNAP/meta/snap.yaml|sed 's/^.*: //')

if [ $CONFINEMENT == "strict" ]; then
  snapcraft-preload $SNAP/bin/oval-xml-feed-merge "$@"
else
  oval-xml-feed-merge "$@"
fi
