#!/usr/bin/env python

"""
Squash github commits starting from a point
"""

import datetime
import logging
from sh import git
from sh import contrib

point = "3e0167c6e723c3c714a4271d6a74c633364aa439"
message = "develop"

logging.basicConfig(level=logging.INFO)


@contrib("git-crypt")
def git_crypt(cmd_in):
    cmd_out = cmd_in.bake(_tty_out=False)
    return cmd_out


from sh import git_crypt  # @UnresolvedImport

git("reset", "--soft", f"{point}")

git("add","--all")

git_crypt("status", "-f")

git("commit", "--quiet", f"--message='{message}'")

git("push", "--force", "--follow-tags")
