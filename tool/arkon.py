#
# build support functions
#

import os
import sys
import subprocess

this_venv = os.environ.get('VIRTUAL_ENV', "")
assert ".pyenv" in this_venv, f"no pyenv: {this_venv}"

try:
    from pip._vendor import tomli as toml
except:
    try:
        from pip._vendor import toml as toml
    except:
        raise RuntimeError("no toml")

project_toml = "pyproject.toml"


def provision_required():
    "ensure pyenv is configured"

    with open(project_toml) as project_file:
        project_data = toml.loads(project_file.read())

    build_bucket:dict = project_data.get("build-system", {})
    build_requires:list = build_bucket.get("requires", [])

    project_bucket:dict = project_data.get("project", {})
    project_core_deps:list = project_bucket.get("dependencies", [])

    optional_deps_dict:dict = project_bucket.get("optional-dependencies", {})
    project_opts_deps = []
    for section in optional_deps_dict.values():
        project_opts_deps.extend(section)

    package_list = build_requires + project_core_deps + project_opts_deps

    command_install = ['pip', 'install'] + package_list
    process = subprocess.run(command_install)
    assert process.returncode == 0


if __name__ == '__main__':
    command = sys.argv[1]
    if command == "provision_required": provision_required()
