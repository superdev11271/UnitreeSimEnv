#!/usr/bin/env python3
"""Publish spawn-relative /dog_odom from absolute /world_pose."""

from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple

import rclpy
from geometry_msgs.msg import Pose
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_srvs.srv import Empty


Vec3 = Tuple[float, float, float]
Quat = Tuple[float, float, float, float]


def normalize_quat(q: Quat) -> Quat:
    x, y, z, w = q
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm < 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    inv = 1.0 / norm
    return (x * inv, y * inv, z * inv, w * inv)


def quat_conjugate(q: Quat) -> Quat:
    x, y, z, w = q
    return (-x, -y, -z, w)


def quat_multiply(q1: Quat, q2: Quat) -> Quat:
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    )


def quat_rotate(q: Quat, v: Vec3) -> Vec3:
    qv = quat_multiply(q, (v[0], v[1], v[2], 0.0))
    result = quat_multiply(qv, quat_conjugate(q))
    return (result[0], result[1], result[2])


def pose_to_tuple(pose: Pose) -> Tuple[Vec3, Quat]:
    p = pose.position
    q = pose.orientation
    return (
        (p.x, p.y, p.z),
        normalize_quat((q.x, q.y, q.z, q.w)),
    )


def relative_pose(
    world_pos: Vec3,
    world_quat: Quat,
    origin_pos: Vec3,
    origin_quat: Quat,
) -> Tuple[Vec3, Quat]:
    origin_inv = quat_conjugate(origin_quat)
    delta = (
        world_pos[0] - origin_pos[0],
        world_pos[1] - origin_pos[1],
        world_pos[2] - origin_pos[2],
    )
    rel_pos = quat_rotate(origin_inv, delta)
    rel_quat = normalize_quat(quat_multiply(origin_inv, world_quat))
    return rel_pos, rel_quat


def world_twist_to_body(
    linear_world: Vec3,
    angular_world: Vec3,
    world_quat: Quat,
) -> Tuple[Vec3, Vec3]:
    body_inv = quat_conjugate(world_quat)
    linear_body = quat_rotate(body_inv, linear_world)
    angular_body = quat_rotate(body_inv, angular_world)
    return linear_body, angular_body


class DogOdomPublisher(Node):
    def __init__(self) -> None:
        super().__init__("dog_odom_publisher")

        self.declare_parameter("world_pose_topic", "/world_pose")
        self.declare_parameter("dog_odom_topic", "/dog_odom")
        self.declare_parameter("set_origin_topic", "/dog_odom/set_origin")
        self.declare_parameter("reset_pose_topic", "/reset")
        self.declare_parameter("reset_service", "/reset_dog_odom")
        self.declare_parameter("odom_frame_id", "odom")
        self.declare_parameter("child_frame_id", "base_link")
        self.declare_parameter("initial_origin_x", 126.079353)
        self.declare_parameter("initial_origin_y", -43.795204)
        self.declare_parameter("initial_origin_z", 2.0)
        self.declare_parameter("initial_origin_yaw", 0.0)

        world_pose_topic = self.get_parameter("world_pose_topic").value
        dog_odom_topic = self.get_parameter("dog_odom_topic").value
        set_origin_topic = self.get_parameter("set_origin_topic").value
        reset_pose_topic = self.get_parameter("reset_pose_topic").value
        reset_service = self.get_parameter("reset_service").value
        self.odom_frame_id = self.get_parameter("odom_frame_id").value
        self.child_frame_id = self.get_parameter("child_frame_id").value

        yaw = float(self.get_parameter("initial_origin_yaw").value)
        self.origin_pos: Vec3 = (
            float(self.get_parameter("initial_origin_x").value),
            float(self.get_parameter("initial_origin_y").value),
            float(self.get_parameter("initial_origin_z").value),
        )
        self.origin_quat: Quat = normalize_quat(
            (0.0, 0.0, math.sin(yaw * 0.5), math.cos(yaw * 0.5))
        )
        self.latest_world_msg: Optional[Odometry] = None

        self.odom_pub = self.create_publisher(Odometry, dog_odom_topic, 10)
        self.create_subscription(Odometry, world_pose_topic, self.world_pose_callback, 10)
        self.create_subscription(Pose, set_origin_topic, self.set_origin_callback, 10)
        self.create_subscription(Pose, reset_pose_topic, self.reset_pose_callback, 10)
        self.create_service(Empty, reset_service, self.reset_service_callback)

        self.get_logger().info(
            f"Publishing {dog_odom_topic} relative to origin "
            f"({self.origin_pos[0]:.3f}, {self.origin_pos[1]:.3f}, {self.origin_pos[2]:.3f})"
        )

    def set_origin_from_pose(self, pose: Pose, reason: str) -> None:
        self.origin_pos, self.origin_quat = pose_to_tuple(pose)
        self.get_logger().info(
            f"dog_odom origin updated ({reason}) at "
            f"({self.origin_pos[0]:.3f}, {self.origin_pos[1]:.3f}, {self.origin_pos[2]:.3f})"
        )
        self.publish_zero_odom()

    def set_origin_callback(self, msg: Pose) -> None:
        self.set_origin_from_pose(msg, "set_origin topic")

    def reset_pose_callback(self, msg: Pose) -> None:
        self.set_origin_from_pose(msg, "/reset topic")

    def reset_service_callback(
        self,
        _request: Empty.Request,
        response: Empty.Response,
    ) -> Empty.Response:
        if self.latest_world_msg is None:
            self.get_logger().warning("reset_dog_odom called before /world_pose was received")
            return response

        self.set_origin_from_pose(self.latest_world_msg.pose.pose, "reset_dog_odom service")
        return response

    def world_pose_callback(self, msg: Odometry) -> None:
        self.latest_world_msg = msg
        self.publish_relative_odom(msg)

    def publish_zero_odom(self) -> None:
        if self.latest_world_msg is None:
            return

        odom = Odometry()
        odom.header.stamp = self.latest_world_msg.header.stamp
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose.orientation.w = 1.0
        self.odom_pub.publish(odom)

    def publish_relative_odom(self, world_msg: Odometry) -> None:
        world_pos, world_quat = pose_to_tuple(world_msg.pose.pose)
        rel_pos, rel_quat = relative_pose(
            world_pos, world_quat, self.origin_pos, self.origin_quat
        )

        linear_world = (
            world_msg.twist.twist.linear.x,
            world_msg.twist.twist.linear.y,
            world_msg.twist.twist.linear.z,
        )
        angular_world = (
            world_msg.twist.twist.angular.x,
            world_msg.twist.twist.angular.y,
            world_msg.twist.twist.angular.z,
        )
        linear_body, angular_body = world_twist_to_body(
            linear_world, angular_world, world_quat
        )

        odom = Odometry()
        odom.header.stamp = world_msg.header.stamp
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose.position.x = rel_pos[0]
        odom.pose.pose.position.y = rel_pos[1]
        odom.pose.pose.position.z = rel_pos[2]
        odom.pose.pose.orientation.x = rel_quat[0]
        odom.pose.pose.orientation.y = rel_quat[1]
        odom.pose.pose.orientation.z = rel_quat[2]
        odom.pose.pose.orientation.w = rel_quat[3]
        odom.twist.twist.linear.x = linear_body[0]
        odom.twist.twist.linear.y = linear_body[1]
        odom.twist.twist.linear.z = linear_body[2]
        odom.twist.twist.angular.x = angular_body[0]
        odom.twist.twist.angular.y = angular_body[1]
        odom.twist.twist.angular.z = angular_body[2]
        self.odom_pub.publish(odom)


def main() -> None:
    rclpy.init()
    node = DogOdomPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
