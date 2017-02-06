#!/bin/bash

output_name=$1
shift
for img in $@; do
  convert $img -resize 520x726! resized_$img
done
i=1
while [[ $@ ]]; do
  first=resized_$1
  shift
  if [[ -z $@ ]]; then
    second=$first
  else
    second=resized_$1
  fi
  shift
  if [[ -z $@ ]]; then
    third=$second
  else
    third=resized_$1
  fi
  convert $first $second $third +append temp_row_$i.jpg
  temp_imgs="$temp_imgs $first $second $third temp_row_$i.jpg"
  i=$((i+1))
  shift
done

table_command="convert"
for j in $(seq 1 $((i-1))); do
  table_command="$table_command temp_row_$j.jpg"
done
table_command="$table_command -append $output_name"
$table_command
rm -rf $temp_imgs
