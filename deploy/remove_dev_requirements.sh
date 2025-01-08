#!/bin/sh

# 检查是否提供了两个参数
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_file> <destination_file>"
    exit 1
fi

SOURCE_FILE=$1
DESTINATION_FILE=$2

# 检查源文件是否存在
if [ ! -f "$SOURCE_FILE" ]; then
    echo "Source file does not exist."
    exit 1
fi

# 使用 awk 来处理文件，当遇到以 "# Dev" 开头的行时停止打印
awk ' /^# Dev/ {exit} {print}' "$SOURCE_FILE" > "$DESTINATION_FILE"

echo "Processed content has been saved to $DESTINATION_FILE"