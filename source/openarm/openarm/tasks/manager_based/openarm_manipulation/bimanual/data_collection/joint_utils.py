# Copyright 2025 Enactic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Joint naming and qpos layout shared with dora-openarm-mujoco / dataset recorder."""

from __future__ import annotations

import torch

from isaaclab.assets import Articulation
from isaaclab.managers import SceneEntityCfg

# Matches dora-openarm-mujoco float32[8]: joints 1-7 + one gripper finger joint.
LEFT_ARM_QPOS_JOINTS = [
    "openarm_left_joint1",
    "openarm_left_joint2",
    "openarm_left_joint3",
    "openarm_left_joint4",
    "openarm_left_joint5",
    "openarm_left_joint6",
    "openarm_left_joint7",
    "openarm_left_finger_joint1",
]

RIGHT_ARM_QPOS_JOINTS = [
    "openarm_right_joint1",
    "openarm_right_joint2",
    "openarm_right_joint3",
    "openarm_right_joint4",
    "openarm_right_joint5",
    "openarm_right_joint6",
    "openarm_right_joint7",
    "openarm_right_finger_joint1",
]

LEFT_ARM_ACTION_JOINTS = LEFT_ARM_QPOS_JOINTS
RIGHT_ARM_ACTION_JOINTS = RIGHT_ARM_QPOS_JOINTS

# dora dataset recorder / opencv-video-capture defaults for wrist cameras.
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 600
CAMERA_UPDATE_PERIOD_S = 1.0 / 30.0

DORA_CAMERA_NAMES = (
    "camera_wrist_right",
    "camera_wrist_left",
    "camera_head_left",
    "camera_head_right",
    "camera_ceiling",
)


def get_arm_qpos(
    robot: Articulation,
    joint_names: list[str],
    env_ids: slice | torch.Tensor | None = None,
) -> torch.Tensor:
    """Read absolute joint positions in dora qpos order (num_envs, 8)."""
    joint_ids, _ = robot.find_joints(joint_names, preserve_order=True)
    qpos = robot.data.joint_pos[:, joint_ids]
    if env_ids is not None:
        qpos = qpos[env_ids]
    return qpos
