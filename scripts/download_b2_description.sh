#!/bin/bash

# Download Unitree B2 robot description from rl_sar_zoo
# Usage: ./download_b2_description.sh [target_dir]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

source "${SCRIPT_DIR}/common.sh"

TARGET_DIR="${1:-src/b2_description}"
ROBOT_DESC_DIR="${PROJECT_ROOT}/${TARGET_DIR}"
REPO_URL="https://github.com/fan-ziqi/rl_sar_zoo.git"
REPO_BRANCH="main"

is_b2_description_valid() {
    [ -d "$ROBOT_DESC_DIR/xacro" ] && [ -f "$ROBOT_DESC_DIR/xacro/robot.xacro" ]
}

print_header "[B2 Description Setup]"

if is_b2_description_valid; then
    print_success "B2 description already exists at ${ROBOT_DESC_DIR}"
    exit 0
fi

if ! check_network_status "github.com"; then
    print_error "B2 description not found and network is unavailable"
    exit 1
fi

print_info "Downloading Unitree B2 description..."

TMP_DIR="$(mktemp -d)"
git clone --depth 1 --filter=blob:none --sparse --branch "$REPO_BRANCH" "$REPO_URL" "$TMP_DIR" || {
    rm -rf "$TMP_DIR"
    print_error "Failed to clone rl_sar_zoo"
    exit 1
}

cd "$TMP_DIR"
git sparse-checkout set b2_description
cd "$PROJECT_ROOT"

rm -rf "$ROBOT_DESC_DIR"
mv "$TMP_DIR/b2_description" "$ROBOT_DESC_DIR"
rm -rf "$TMP_DIR"

if ! is_b2_description_valid; then
    print_error "B2 description installation failed"
    exit 1
fi

print_success "B2 description setup completed!"
print_info "Installation path: ${ROBOT_DESC_DIR}"
