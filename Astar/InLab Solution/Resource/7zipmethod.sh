#!/bin/bash
find ./ -type f -iname "*.mth" | while read filename;do
    onlyname="$(basename $filename)"
    echo $HOME/.vim/tools/7z.exe a -tzip "$onlyname.pzm" -plcj2346026 "$filename"
done

#find ./ -type f -iname "*.inc" | while read filename;do
#done
