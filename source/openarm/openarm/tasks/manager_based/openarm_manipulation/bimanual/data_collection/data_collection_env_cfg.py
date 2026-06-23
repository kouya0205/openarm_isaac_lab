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

"""Isaac Lab environment for bimanual OpenArm teleoperation data collection."""

from dataclasses import MISSING

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedEnvCfg
from isaaclab.managers import ActionTermCfg as ActionTerm
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import GroundPlaneCfg, UsdFileCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from . import mdp
from .joint_utils import CAMERA_HEIGHT, CAMERA_UPDATE_PERIOD_S, CAMERA_WIDTH

##
# Scene
##


def _make_camera_cfg(prim_path: str, offset: CameraCfg.OffsetCfg) -> CameraCfg:
    """Pinhole camera matching dora recorder resolution and ~30 Hz update rate."""
    return CameraCfg(
        prim_path=prim_path,
        update_period=CAMERA_UPDATE_PERIOD_S,
        height=CAMERA_HEIGHT,
        width=CAMERA_WIDTH,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=400.0,
            horizontal_aperture=20.955,
            clipping_range=(0.01, 20.0),
        ),
        offset=offset,
    )


@configclass
class DataCollectionSceneCfg(InteractiveSceneCfg):
    """Bimanual OpenArm cell scene with five dataset cameras."""

    # ground
    ground = AssetBaseCfg(
        prim_path="/World/GroundPlane",
        init_state=AssetBaseCfg.InitialStateCfg(pos=[0.0, 0.0, -1.05]),
        spawn=GroundPlaneCfg(),
    )

    # table (demo-style manipulation workspace)
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        init_state=AssetBaseCfg.InitialStateCfg(pos=[0.55, 0.0, 0.0], rot=[0.707, 0.0, 0.0, 0.707]),
        spawn=UsdFileCfg(usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Mounts/SeattleLabTable/table_instanceable.usd"),
    )

    robot: ArticulationCfg = MISSING

    # Camera names match dora-openarm-mujoco / dataset recorder outputs.
    # Positions are initial estimates; calibrate against MuJoCo demo scene in Phase 3.
    camera_wrist_right = _make_camera_cfg(
        prim_path="{ENV_REGEX_NS}/Robot/openarm_right_link7/camera_wrist_right",
        offset=CameraCfg.OffsetCfg(pos=(0.05, 0.0, 0.04), rot=(0.5, -0.5, 0.5, -0.5), convention="ros"),
    )
    camera_wrist_left = _make_camera_cfg(
        prim_path="{ENV_REGEX_NS}/Robot/openarm_left_link7/camera_wrist_left",
        offset=CameraCfg.OffsetCfg(pos=(0.05, 0.0, 0.04), rot=(0.5, -0.5, 0.5, -0.5), convention="ros"),
    )
    camera_head_left = _make_camera_cfg(
        prim_path="{ENV_REGEX_NS}/Cameras/camera_head_left",
        offset=CameraCfg.OffsetCfg(pos=(0.0, 0.18, 1.35), rot=(0.707, 0.0, 0.707, 0.0), convention="ros"),
    )
    camera_head_right = _make_camera_cfg(
        prim_path="{ENV_REGEX_NS}/Cameras/camera_head_right",
        offset=CameraCfg.OffsetCfg(pos=(0.0, -0.18, 1.35), rot=(0.707, 0.0, 0.707, 0.0), convention="ros"),
    )
    camera_ceiling = _make_camera_cfg(
        prim_path="{ENV_REGEX_NS}/Cameras/camera_ceiling",
        offset=CameraCfg.OffsetCfg(pos=(0.55, 0.0, 1.85), rot=(0.0, 1.0, 0.0, 0.0), convention="ros"),
    )

    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(color=(0.75, 0.75, 0.75), intensity=3000.0),
    )


##
# MDP
##


@configclass
class ActionsCfg:
    """Absolute joint targets in dora qpos layout (8 + 8)."""

    left_arm_action: ActionTerm = MISSING
    right_arm_action: ActionTerm = MISSING


@configclass
class ObservationsCfg:
    """Observations used by the dora Isaac bridge and local verification."""

    @configclass
    class RecordingCfg(ObsGroup):
        """Arm state and RGB cameras for dataset recording."""

        left_arm_qpos = ObsTerm(func=mdp.left_arm_qpos)
        right_arm_qpos = ObsTerm(func=mdp.right_arm_qpos)

        camera_wrist_right = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("camera_wrist_right"), "data_type": "rgb", "normalize": False},
        )
        camera_wrist_left = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("camera_wrist_left"), "data_type": "rgb", "normalize": False},
        )
        camera_head_left = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("camera_head_left"), "data_type": "rgb", "normalize": False},
        )
        camera_head_right = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("camera_head_right"), "data_type": "rgb", "normalize": False},
        )
        camera_ceiling = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("camera_ceiling"), "data_type": "rgb", "normalize": False},
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    recording: RecordingCfg = RecordingCfg()


@configclass
class EventCfg:
    """Reset the robot to its default keyframe without domain randomization."""

    reset_robot_joints = EventTerm(
        func=mdp.reset_joints_by_scale,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "position_range": (1.0, 1.0),
            "velocity_range": (0.0, 0.0),
        },
    )


@configclass
class DataCollectionEnvCfg(ManagerBasedEnvCfg):
    """Manager-based environment for Isaac Sim teleoperation data collection."""

    scene: DataCollectionSceneCfg = DataCollectionSceneCfg(num_envs=1, env_spacing=2.5)
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    events: EventCfg = EventCfg()

    def __post_init__(self):
        # 500 Hz control loop to match dora quittable-tick-leader (2 ms).
        self.decimation = 1
        self.sim.dt = 0.002
        self.sim.render_interval = max(1, int(round(1.0 / (30.0 * self.sim.dt))))
        self.viewer.eye = (2.0, 2.0, 1.8)
        self.viewer.lookat = (0.55, 0.0, 0.9)
