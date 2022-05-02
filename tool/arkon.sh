#!/usr/bin/env bash

#
# ensure project pyenv active
#

set -e -u

readonly this_dir=$( dirname "$0" )
readonly base_dir=$( cd $this_dir/.. && pwd )
readonly pyenv_dir=$base_dir/.pyenv

readonly base_main_dir=$base_dir/src/main 
readonly base_test_dir=$base_dir/src/test 

cd $base_dir

if [ ! -d $pyenv_dir ] ; then
    echo "### venv init"
    mkdir -p $pyenv_dir
    python -m venv $pyenv_dir
fi 

source $pyenv_dir/bin/activate

echo "### base_dir=$base_dir"
echo "### pyenv_dir=$pyenv_dir"
