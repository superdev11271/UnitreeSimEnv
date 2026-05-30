#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/scripts/common.sh"

setup_b2_description() {
    print_header "[Setting up B2 Description]"
    bash "${SCRIPT_DIR}/scripts/download_b2_description.sh" || {
        print_error "Failed to setup B2 description"
        exit 1
    }
}

setup_gazebo_models() {
    local script="${SCRIPT_DIR}/scripts/download_gazebo_models.sh"
    if [ -f "$script" ]; then
        bash "$script" || print_warning "Gazebo models setup skipped (optional)"
    fi
}

create_ros2_package_symlinks() {
    print_header "[Creating ROS2 package.xml symlinks]"

    while IFS= read -r -d '' package_dir; do
        package_dir="$(dirname "$package_dir")"
        if [ -f "$package_dir/package.ros2.xml" ]; then
            rm -f "$package_dir/package.xml"
            ln -sf package.ros2.xml "$package_dir/package.xml"
        fi
    done < <(find "${SCRIPT_DIR}/src" -name "package.ros2.xml" -print0)

    print_success "ROS2 package symlinks created"
}

run_ros_build() {
    print_header "[Running ROS2 Build]"

    if [ -z "$ROS_DISTRO" ]; then
        print_error "ROS environment not detected. Source your ROS setup first."
        exit 1
    fi

    cd "$SCRIPT_DIR"
    colcon build --merge-install --symlink-install "$@"
    print_success "ROS2 build completed!"
}

clean_workspace() {
    print_header "[Cleaning Workspace]"
    cd "$SCRIPT_DIR"
    rm -rf build/ install/ log/
    find src -name "package.xml" -type l -delete
    print_success "Clean completed!"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --clean   Remove build artifacts and package.xml symlinks"
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

    setup_b2_description
    setup_gazebo_models
    create_ros2_package_symlinks
    run_ros_build "$@"
}

main "$@"
