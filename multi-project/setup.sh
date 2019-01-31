#!/usr/bin/env bash

mkdir -p build/libfoo
mkdir -p build/bar

pushd build/libfoo
  cmake ../../source/libfoo -DCMAKE_EXPORT_COMPILE_COMMANDS=On -DCMAKE_BUILD_TYPE=Debug
  make
popd

pushd build/bar
  cmake ../../source/bar -DCMAKE_EXPORT_COMPILE_COMMANDS=On -DCMAKE_BUILD_TYPE=Debug
  make
popd
