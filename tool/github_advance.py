#!/usr/bin/env python

"""
Squash github commits starting from a point
"""

import datetime
import logging
from sh import git
from sh import contrib

logging.basicConfig(level=logging.INFO)


@contrib("git-crypt")
def git_crypt(cmd_in):
    cmd_out = cmd_in.bake(_tty_out=False)
    return cmd_out


from sh import git_crypt  # @UnresolvedImport

instant = datetime.datetime.now().isoformat()
message = f"develop {instant}"

git("add", "--all")

git_crypt("status", "-f")

git("commit", "--quiet", f"--message='{message}'")

git(f"push")
