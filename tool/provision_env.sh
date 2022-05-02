#!/usr/bin/env bash

#
# provision development venv
#

source ./arkon.sh 

python $this_dir/arkon.py provision_required
