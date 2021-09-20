#!/bin/bash

cd "$(dirname "$0")"
cd v-hacd/bin/
cmake ../src/ $1
make -j 4
