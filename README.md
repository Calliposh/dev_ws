# Autonomous Mobile Robot (AMR)

ROS 2 workspace for an autonomous mobile robot prototype with wheel
odometry, LiDAR-based mapping, localization, and autonomous navigation.

## System Architecture

### Jetson Nano
- Arduino sensor bridge.
- Wheel-encoder odometry.
- YDLIDAR X3 Pro driver.
- Hardware-facing ROS 2 nodes.

### Laptop
- Robot description and TF publishing.
- SLAM Toolbox for physical mapping.
- Robot Localization EKF for filtered wheel odometry.
- Nav2 for localization and autonomous navigation.
- RViz for visualization.

Both machines must use compatible ROS 2 environments and matching
`ROS_DOMAIN_ID` settings. The physical bring-up guide uses domain ID `10`.

## Repository Packages

### `my_robot_description`
Contains the robot URDF/Xacro description, launch files, RViz and
simulation resources, SLAM Toolbox configuration, Nav2 configuration,
and EKF configuration.

### `amr_hardware`
Contains the Arduino sensor bridge and wheel-encoder odometry node,
including the wheel-odometry launch configuration.

## Odometry and TF

The intended physical odometry data flow is:

`Wheel encoders → /wheel/odom → EKF → /odom`

The wheel-odometry node publishes raw measurements to `/wheel/odom`
without publishing the odometry transform when launched with the
provided EKF-compatible launch configuration.

The EKF publishes filtered odometry on `/odom` and owns the
`odom → base_footprint` transform. The robot description provides the
robot's fixed transforms, including the base-to-LiDAR relationship.

The MPU6050 IMU is currently disabled and is not fused by the EKF.
Consequently, the filtered estimate still depends on wheel odometry and
does not eliminate accumulated wheel-odometry drift.

## Physical Bring-Up

Follow the detailed guide:

[`docs/physical_amr_bringup.md`](docs/physical_amr_bringup.md)

The guide covers environment setup, hardware-facing nodes, TF,
physical SLAM mapping, map saving, EKF startup, and Nav2 bring-up.

## Build

On a machine with the required ROS 2 dependencies installed, from the
workspace root:

```bash
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Validation Status

The repository contains the configuration and launch files for the
AMR's hardware interface, physical mapping, localization, and navigation.

The latest EKF integration has been reviewed at the source level but
has not been runtime-tested after these changes. Before deployment,
build the workspace in a ROS 2 Humble environment and verify the EKF,
distributed ROS 2 communication, TF tree, and autonomous navigation.