#!/usr/bin/env bash
set -euxo pipefail

OUTDIR="src/uncms/static/uncms/vendor/trumbowyg"
VERSION=2.26.0
DELETE_PLUGINS="
  allowtagsfrompaste base64 colors emoji fontfamily fontsize giphy history
  indent insertaudio lineheight mathml mention noembed pasteembed pasteimage
  resizimg ruby specialchars template
"

# rm -rf "$OUTDIR"

# ziptmp=$(mktemp)
# extracttmp=$(mktemp -d)
# wget -O "$ziptmp" "https://github.com/Alex-D/Trumbowyg/archive/refs/tags/v$VERSION.zip"
# ls -l "$ziptmp"
# file "$ziptmp"
# unzip "$ziptmp" "Trumbowyg-$VERSION/dist/*" -d "$extracttmp"

# # Copy over the files
# mv "$extracttmp/Trumbowyg-$VERSION/dist" "$OUTDIR"
find "$OUTDIR" -name "*.min.css" -exec rm -rf {} \;
find "$OUTDIR" -name "*.min.css.map" -exec rm -rf {} \;
find "$OUTDIR" -name "*.min.js" -exec rm -rf {} \;
find "$OUTDIR" -name "sass" -exec rm -rf {} \;

for plugin in $DELETE_PLUGINS; do
    rm -rf "$OUTDIR/plugins/$plugin"
done
