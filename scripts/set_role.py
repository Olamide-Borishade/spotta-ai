"""One-off script: promote or demote a user's role.

Usage:
    python scripts/set_role.py <username> <user|betatester|admin>
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db import VALID_ROLES, init_db, set_user_role  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set a user's role.")
    parser.add_argument("username")
    parser.add_argument("role", choices=VALID_ROLES)
    args = parser.parse_args()

    init_db()
    set_user_role(args.username, args.role)
    print(f"Set {args.username!r} to role {args.role!r}")
