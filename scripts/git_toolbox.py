#!/usr/bin/env python3
# ==============================================================================
# Filename    : git_toolbox.py
# Version     : 2.0.0
# Description : Local Git utilities for manifest, changelog, and WIP blocking.
#               Default: changelog grouped by date.
#               Future: tag-based changelog available (commented out).
# ==============================================================================

import subprocess
import sys
from collections import defaultdict

BRANCH = "main"
RECENT_LIMIT = 5

def get_commits():
    log_format = "%H|%ad|%an|%s"
    cmd = ["git", "log", BRANCH, "--pretty=format:" + log_format, "--date=short"]
    output = subprocess.check_output(cmd, text=True)
    return [line.strip() for line in output.splitlines()]

def build_changelog():
    commits = get_commits()
    with open("CHANGELOG.md", "w") as f:
        f.write("# CHANGELOG\n\n")

        # -------------------------
        # Current Mode: Date-based
        # -------------------------
        grouped = defaultdict(list)
        for line in commits:
            _, date, author, msg = line.split("|", 3)
            grouped[date].append((msg, author))

        f.write("## Summary (Last 5 Commits)\n\n")
        for line in commits[:RECENT_LIMIT]:
            _, date, author, msg = line.split("|", 3)
            f.write(f"- {date} — {msg} — Author: {author}\n")
        f.write("\n## Full History\n\n")

        for date in sorted(grouped.keys(), reverse=True):
            f.write(f"### {date}\n\n")
            for msg, author in grouped[date]:
                f.write(f"- {msg} — {author}\n")
            f.write("\n")

        # -------------------------
        # Future Mode: Tag-based
        # -------------------------
        # To switch, comment out the date-based block above
        # and uncomment this one:
        #
        # tag_cmd = ["git", "tag", "--sort=-creatordate"]
        # tags = subprocess.check_output(tag_cmd, text=True).splitlines()
        #
        # for tag in tags:
        #     f.write(f"## {tag}\n\n")
        #     tag_log_cmd = [
        #         "git", "log", f"{tag}^..{tag}",
        #         "--pretty=format:%ad|%an|%s", "--date=short"
        #     ]
        #     tag_output = subprocess.check_output(tag_log_cmd, text=True).splitlines()
        #     for line in tag_output:
        #         date, author, msg = line.split("|", 2)
        #         f.write(f"- {date} — {msg} — Author: {author}\n")
        #     f.write("\n")

    print("✅ CHANGELOG.md updated.")

def build_manifest():
    added = defaultdict(list)
    deleted = defaultdict(list)
    recent_changes = []

    cmd = ["git", "log", BRANCH, "--name-status", "--date=short", "--pretty=format:%H|%ad|%s"]
    log_lines = subprocess.check_output(cmd, text=True).splitlines()

    current_commit = {}
    for line in log_lines:
        if "|" in line:
            parts = line.strip().split("|", 2)
            if len(parts) == 3:
                current_commit = {
                    "hash": parts[0],
                    "date": parts[1],
                    "msg": parts[2]
                }
        elif line.startswith(("A", "D")):
            status, path = line.split(maxsplit=1)
            entry = f"{current_commit['date']} — {current_commit['msg']}"
            if status == "A":
                added[path].append(entry)
                recent_changes.append(f"{current_commit['date']} — Added {path} — \"{current_commit['msg']}\"")
            elif status == "D":
                deleted[path].append(entry)
                recent_changes.append(f"{current_commit['date']} — Deleted {path} — \"{current_commit['msg']}\"")

    with open("MANIFEST.md", "w") as f:
        f.write("# MANIFEST\n\n")

        f.write("## Current Files\n\n")
        current_files = subprocess.check_output(
            ["git", "ls-tree", "-r", BRANCH, "--name-only"], text=True
        ).splitlines()
        for path in sorted(current_files):
            f.write(f"📄 {path}\n")
            if path in added:
                for entry in added[path]:
                    f.write(f"  Added: {entry}\n")
            f.write("\n")

        f.write("## Recent Changes (Last 5)\n\n")
        for line in recent_changes[:RECENT_LIMIT]:
            f.write(f"- {line}\n")
        f.write("\n")

        f.write("## Full File History\n\n")
        all_paths = sorted(set(list(added.keys()) + list(deleted.keys())))
        for path in all_paths:
            f.write(f"📄 {path}\n")
            if path in added:
                for entry in added[path]:
                    f.write(f"  Added: {entry}\n")
            if path in deleted:
                for entry in deleted[path]:
                    f.write(f"  Deleted: {entry}\n")
            f.write("\n")

    print("✅ MANIFEST.md updated.")

def check_wip():
    for line in get_commits():
        _, _, _, msg = line.split("|", 3)
        if "WIP" in msg.upper():
            print(f"❌ Push blocked due to WIP commit: {msg}")
            sys.exit(1)
    print("✅ No WIP commits found.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python git_toolbox.py [manifest|changelog|check-wip]")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action == "manifest":
        build_manifest()
    elif action == "changelog":
        build_changelog()
    elif action == "check-wip":
        check_wip()
    else:
        print("Invalid command. Use one of: manifest, changelog, check-wip")
        sys.exit(1)

