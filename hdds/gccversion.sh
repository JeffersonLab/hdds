#!/bin/sh
gcc -v 2>&1 | awk '/gcc version/ {print $3}' | awk -F. '{print $1}'
