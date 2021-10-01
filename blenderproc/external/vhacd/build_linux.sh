#!/bin/bash

cd $1
cd bin/
cmake ../src/ $2
make -j 4
