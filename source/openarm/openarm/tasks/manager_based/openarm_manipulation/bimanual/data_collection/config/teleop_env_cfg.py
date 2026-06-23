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

"""Concrete OpenArm bimanual data-collection environment configuration."""

from isaaclab.assets.articulation import ArticulationCfg
from isaaclab.utils import configclass

from openarm.tasks.manager_based.openarm_manipulation.assets.openarm_bimanual import OPEN_ARM_HIGH_PD_CFG

from .. import mdp
from ..data_collection_env_cfg import DataCollectionEnvCfg
from ..joint_utils import LEFT_ARM_ACTION_JOINTS, RIGHT_ARM_ACTION_JOINTS

##
# Environment configuration
##


@configclass
class OpenArmDataCollectionEnvCfg(DataCollectionEnvCfg):
    """Bimanual OpenArm environment for dora-based teleoperation data collection."""

    def __post_init__(self):
        super().__post_init__()

        self.scene.robot = OPEN_ARM_HIGH_PD_CFG.replace(
            prim_path="{ENV_REGEX_NS}/Robot",
            init_state=ArticulationCfg.InitialStateCfg(
                joint_pos={
                    "openarm_left_joint1": 0.0,
                    "openarm_left_joint2": 0.0,
                    "openarm_left_joint3": 0.0,
                    "openarm_left_joint4": 0.0,
                    "openarm_left_joint5": 0.0,
                    "openarm_left_joint6": 0.0,
                    "openarm_left_joint7": 0.0,
                    "openarm_right_joint1": 0.0,
                    "openarm_right_joint2": 0.0,
                    "openarm_right_joint3": 0.0,
                    "openarm_right_joint4": 0.0,
                    "openarm_right_joint5": 0.0,
                    "openarm_right_joint6": 0.0,
                    "openarm_right_joint7": 0.0,
                    "openarm_left_finger_joint.*": 0.044,
                    "openarm_right_finger_joint.*": 0.044,
                },
            ),
        )

        # Absolute joint targets: matches dora float32[8] per arm (no offset/scale).
        self.actions.left_arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=LEFT_ARM_ACTION_JOINTS,
            scale=1.0,
            use_default_offset=False,
        )
        self.actions.right_arm_action = mdp.JointPositionActionCfg(
            asset_name="robot",
            joint_names=RIGHT_ARM_ACTION_JOINTS,
            scale=1.0,
            use_default_offset=False,
        )


@configclass
class OpenArmDataCollectionEnvCfg_PLAY(OpenArmDataCollectionEnvCfg):
    """Play/verification variant with GUI-friendly render cadence."""

    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 1
        self.sim.render_interval = 2
