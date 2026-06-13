#!/usr/bin/env python3

import sys
import time

import rclpy
from controller_manager import (
    configure_controller,
    list_controllers,
    load_controller,
    switch_controllers,
)
from controller_manager.controller_manager_services import ServiceNotFoundError
from rclpy.node import Node

CONTROLLER_NAME = "joint_state_broadcaster"
CONTROLLER_MANAGER = "/controller_manager"
SERVICE_TIMEOUT = 180.0
CALL_TIMEOUT = 180.0
SWITCH_TIMEOUT = 120.0


def is_loaded(node: Node) -> bool:
    response = list_controllers(
        node,
        CONTROLLER_MANAGER,
        SERVICE_TIMEOUT,
        CALL_TIMEOUT,
    )
    return any(controller.name == CONTROLLER_NAME for controller in response.controller)


def main() -> int:
    rclpy.init()
    node = Node("load_joint_state_broadcaster")

    try:
        deadline = time.monotonic() + SERVICE_TIMEOUT
        while time.monotonic() < deadline:
            try:
                if is_loaded(node):
                    node.get_logger().info(
                        f"{CONTROLLER_NAME} already loaded, skipping load_controller"
                    )
                    break

                response = load_controller(
                    node,
                    CONTROLLER_MANAGER,
                    CONTROLLER_NAME,
                    SERVICE_TIMEOUT,
                    CALL_TIMEOUT,
                )
                if response.ok:
                    node.get_logger().info(f"Loaded {CONTROLLER_NAME}")
                    break

                if is_loaded(node):
                    node.get_logger().info(
                        f"{CONTROLLER_NAME} loaded by a previous slow request, continuing"
                    )
                    break

                node.get_logger().error(
                    f"Failed loading {CONTROLLER_NAME}: {response}"
                )
                return 1
            except ServiceNotFoundError:
                node.get_logger().info(
                    f"Waiting for {CONTROLLER_MANAGER} services..."
                )
                time.sleep(1.0)
        else:
            node.get_logger().error(
                f"Timed out waiting for {CONTROLLER_MANAGER} after {SERVICE_TIMEOUT}s"
            )
            return 1

        response = configure_controller(
            node,
            CONTROLLER_MANAGER,
            CONTROLLER_NAME,
            SERVICE_TIMEOUT,
            CALL_TIMEOUT,
        )
        if not response.ok:
            node.get_logger().error(f"Failed to configure {CONTROLLER_NAME}")
            return 1

        response = switch_controllers(
            node,
            CONTROLLER_MANAGER,
            [],
            [CONTROLLER_NAME],
            True,
            True,
            SWITCH_TIMEOUT,
            CALL_TIMEOUT,
        )
        if not response.ok:
            node.get_logger().error(f"Failed to activate {CONTROLLER_NAME}")
            return 1

        node.get_logger().info(f"Configured and activated {CONTROLLER_NAME}")
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
