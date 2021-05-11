#!/bin/bash

cd "$(dirname "$0")"
cd v-hacd/bin/
cmake ../src/
make -j 4