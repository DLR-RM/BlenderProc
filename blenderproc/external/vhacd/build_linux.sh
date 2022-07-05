#!/bin/bash

cd $1
cd app/
cmake CMakeLists.txt
cmake --build .