#!/bin/bash

# All of these just to get the directory where this script is located
pushd . > /dev/null
SCRIPT_PATH="${BASH_SOURCE[0]}";
  while([ -h "${SCRIPT_PATH}" ]) do 
    cd "`dirname "${SCRIPT_PATH}"`"
    SCRIPT_PATH="$(readlink "`basename "${SCRIPT_PATH}"`")"; 
  done
cd "`dirname "${SCRIPT_PATH}"`" > /dev/null
SCRIPT_PATH="`pwd`";
popd  > /dev/null

if which python2 > /dev/null
then
    PYTHON_EXECUTABLE=python2
else
    PYTHON_EXECUTABLE=python
fi

export PYTHONPATH="$PYTHONPATH:$SCRIPT_PATH"

exec $PYTHON_EXECUTABLE -m lasana_uploader.lasana $*
