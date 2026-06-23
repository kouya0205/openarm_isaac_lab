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

"""Observation helpers for teleoperation data collection."""

from __future__ import annotations

import torch

from isaaclab.assets import Articulation
from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers import SceneEntityCfg

from ..joint_utils import LEFT_ARM_QPOS_JOINTS, RIGHT_ARM_QPOS_JOINTS, get_arm_qpos


def left_arm_qpos(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Left arm qpos in dora layout (num_envs, 8)."""
    robot: Articulation = env.scene[asset_cfg.name]
    return get_arm_qpos(robot, LEFT_ARM_QPOS_JOINTS)


def right_arm_qpos(env: ManagerBasedEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Right arm qpos in dora layout (num_envs, 8)."""
    robot: Articulation = env.scene[asset_cfg.name]
    return get_arm_qpos(robot, RIGHT_ARM_QPOS_JOINTS)
