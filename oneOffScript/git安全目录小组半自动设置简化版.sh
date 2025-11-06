#!/bin/bash


GROUP_NAME="gksd-team"
REPO_BASE="/mnt/raid10"

for repo in $(find $REPO_BASE -name "*.git" -type d); do
    if [ -d "$repo/objects" ] && [ -d "$repo/refs" ]; then
        echo "配置仓库: $repo"
        for user in $(getent group $GROUP_NAME | cut -d: -f4 | tr ',' ' '); do
            sudo -u $user git config --global --add safe.directory "$repo" 2>/dev/null && echo "  ✓ $user" || echo "  ✗ $user"
        done
    fi
done
