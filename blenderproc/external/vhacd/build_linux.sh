#!/bin/bash

cd $1
cd app/
cmake CmakeLists.txt -DCMAKE_BUILD_TYPE=Release
cmake --build .