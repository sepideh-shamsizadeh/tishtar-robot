# TISHTAR — Chassis & Wheel Measurements

**Project:** TISHTAR Autonomous Mobile Robot  
**Related issue:** [#17 — Robot Description & RViz Visualization](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/17)  
**Measurement date:** 18 November 2026  
**Status:** Initial measurements — some dimensions require verification

## 1. Overview

This document records the physical dimensions of TISHTAR's four-wheel mobile robot chassis.

These measurements will be used to develop the ROS 2 URDF/Xacro robot description, configure coordinate frames, and visualize the robot in RViz.

All measurements were taken manually. Dimensions are recorded in centimetres and converted to metres for ROS 2.

## 2. Chassis Dimensions

| Parameter | Measurement | Metres |
|---|---:|---:|
| Chassis longitudinal length (red line) | 24 cm | 0.240 |
| Chassis upper width (blue line) | 15 cm | 0.150 |
| Chassis middle width (green line) | 14 cm | 0.140 |
| Chassis side length (yellow line) | 23 cm | 0.230 |
| Ground to second chassis layer | 13.5 cm | 0.135 |

**Notes:**
- The chassis has curved front and rear edges and a slightly varying width.
- The initial URDF will use simplified rectangular geometry.
- Plate thickness and the precise positions of the chassis layers still need to be measured.

## 3. Wheel Dimensions

| Parameter | Measurement | Metres |
|---|---:|---:|
| Wheel outer diameter | 7 cm | 0.070 |
| Wheel radius | 3.5 cm | 0.035 |
| Wheelbase (front-to-rear centers) | 17.5 cm | 0.175 |
| Wheel track (left-to-right centers) | 22 cm | 0.220 |
| Wheel axial width | TBD | TBD |

The robot has four wheels with angled rollers (mecanum-style wheels).

For initial RViz visualization, the wheels will be approximated using cylinders. Accurate roller geometry and wheel kinematics can be modeled later if required.

## 4. Proposed ROS Coordinate System

Following ROS REP-103:

- X: Forward
- Y: Left
- Z: Up
- Right-handed coordinate system
- Distances in metres
- Angles in radians

The initial model assumes `base_link` is horizontally centered between the four wheel centers.

The robot's forward direction must be physically confirmed.

## 5. Proposed Wheel Coordinates

Assuming symmetric wheel placement:

- Half wheelbase = 0.175 / 2 = 0.0875 m
- Half track width = 0.220 / 2 = 0.1100 m

| Wheel | X (m) | Y (m) | Z (m) |
|---|---:|---:|---|
| Front left | +0.0875 | +0.1100 | TBD |
| Front right | +0.0875 | -0.1100 | TBD |
| Rear left | -0.0875 | +0.1100 | TBD |
| Rear right | -0.0875 | -0.1100 | TBD |

These positions are provisional until the forward direction, symmetry, and `base_link` vertical origin are confirmed.

## 6. Initial URDF Parameters

```xml
<xacro:property name="chassis_length" value="0.24"/>
<xacro:property name="chassis_width" value="0.14"/>

<xacro:property name="wheel_radius" value="0.035"/>
<xacro:property name="wheelbase" value="0.175"/>
<xacro:property name="wheel_track" value="0.220"/>
```

The chassis width is a simplified value for initial visualization, not the maximum measured width.

## 7. Remaining Measurements

- [ ] Chassis plate thickness
- [ ] Wheel axial width
- [ ] Vertical position of `base_link`
- [ ] Exact height of individual chassis layers
- [ ] Camera pan pivot position
- [ ] Camera tilt pivot position
- [ ] Camera optical center offset
- [ ] TF Mini LiDAR mounting position
- [ ] IMU mounting position and orientation
- [ ] Ultrasonic sensor mounting position
- [ ] Verify front direction and wheel ordering

The future 4D LiDAR will be documented separately once its mounting configuration is finalized.

## 8. Validation

The measurements will be validated against the physical robot and the initial model in RViz.

The first milestone is a simplified chassis-and-four-wheels URDF with correct overall proportions and internally consistent coordinate frames.

Any later physical changes should be reflected in this document and in the Xacro parameters.