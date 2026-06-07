#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

COLOR_ERROR='\033[0;31m'
COLOR_SUCCESS='\033[0;32m'
COLOR_INFO='\033[0;34m'
COLOR_RESET='\033[0m'

print_success() {
    echo -e "${COLOR_SUCCESS}[SUCCESS]${COLOR_RESET} $1"
}

print_error() {
    echo -e "${COLOR_ERROR}[ERROR]${COLOR_RESET} $1"
}

print_header() {
    echo -e "${COLOR_INFO}-------------------------------------------------------------------${COLOR_RESET}"
    echo -e "${COLOR_INFO}$1${COLOR_RESET}"
}

run_ros_build() {
    print_header "[Running ROS 2 Build]"

    if [ -z "$ROS_DISTRO" ]; then
        print_error "ROS 2 environment not detected. Source /opt/ros/humble/setup.bash first."
        exit 1
    fi

    cd "$SCRIPT_DIR"
    colcon build --merge-install --symlink-install "$@"
    print_success "ROS 2 build completed!"
}

clean_workspace() {
    print_header "[Cleaning Workspace]"
    cd "$SCRIPT_DIR"
    rm -rf build/ install/ log/
    print_success "Clean completed!"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --clean   Remove build artifacts"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0            Build the B2 simulation workspace"
    echo "  $0 -c         Clean build artifacts"
}

main() {
    case "${1:-}" in
        -c|--clean) clean_workspace; exit 0 ;;
        -h|--help) show_usage; exit 0 ;;
    esac

    run_ros_build "$@"
}

main "$@"
