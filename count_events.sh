#!/usr/bin/bash

cat $1 | sort | uniq -c > $1.counts

