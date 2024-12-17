#!/bin/sh

if [ -z "$1" ]; then
    echo "Usage: $0 filename"
    exit 1
fi

filename=$1
tempfile=$2

if [ ! -f "$filename" ]; then
    echo "File not found: $filename"
    exit 1
fi

> "$tempfile"

in_comment_block=false
while read -r line; do
    if [ "$in_comment_block" = false ] && [ "$line" = "# Dev"* ]; then
        in_comment_block=true
        echo "$line" >> "$tempfile"
    elif [ "$in_comment_block" = true ]; then
        echo "# $line" >> "$tempfile"
    else
        echo "$line" >> "$tempfile"
    fi
done < "$filename"

echo "Processed content saved to: $tempfile"