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

"""Gym registration and helpers for bimanual data-collection environments."""

from __future__ import annotations

import gymnasium as gym

from isaaclab.envs import ManagerBasedEnv, ManagerBasedEnvCfg
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg


def create_data_collection_env(
    task: str,
    *,
    device: str = "cuda:0",
    num_envs: int = 1,
    cfg: ManagerBasedEnvCfg | None = None,
) -> ManagerBasedEnv:
    """Create a data-collection environment.

    Use this helper instead of ``gym.make()``. :class:`ManagerBasedEnv` is not a
    :class:`gymnasium.Env` subclass, so ``gym.make`` rejects it even though the
    simulation itself initializes correctly.
    """
    if cfg is None:
        cfg = parse_env_cfg(task, device=device, num_envs=num_envs)
    else:
        cfg.sim.device = device
        cfg.scene.num_envs = num_envs
    return ManagerBasedEnv(cfg=cfg)


def _gym_make_not_supported(*_args, **_kwargs):
    raise RuntimeError(
        "Isaac-Data-Collection-OpenArm-Bi tasks do not support gym.make(). "
        "Use create_data_collection_env(task_name) instead."
    )


# Registration exposes env_cfg_entry_point for parse_env_cfg / list_envs.
gym.register(
    id="Isaac-Data-Collection-OpenArm-Bi-v0",
    entry_point=f"{__name__}:_gym_make_not_supported",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.teleop_env_cfg:OpenArmDataCollectionEnvCfg",
    },
)

gym.register(
    id="Isaac-Data-Collection-OpenArm-Bi-Play-v0",
    entry_point=f"{__name__}:_gym_make_not_supported",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.teleop_env_cfg:OpenArmDataCollectionEnvCfg_PLAY",
    },
)
