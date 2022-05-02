#!/usr/bin/env bash

#
#
#

source ./arkon.sh 

export PYTHONPATH=$base_main_dir:$base_test_dir

command_pytest=(
    pytest
    --verbose
#    --last-failed
    $base_dir/src
    
)

${command_pytest[@]}
