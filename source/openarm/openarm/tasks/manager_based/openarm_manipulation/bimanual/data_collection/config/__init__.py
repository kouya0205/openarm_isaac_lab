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

"""Gym registration for bimanual data-collection environments."""

from __future__ import annotations

import importlib

import gymnasium as gym

from isaaclab.envs import ManagerBasedEnv


def make_manager_based_env(env_cfg_entry_point: str, cfg=None, **kwargs):
    """Gymnasium factory for :class:`ManagerBasedEnv`.

    Unlike :class:`ManagerBasedRLEnv`, the base environment only accepts ``cfg``.
    ``env_cfg_entry_point`` is kept in registration kwargs for ``parse_env_cfg``.
    """
    del kwargs  # render_mode and other gym.make kwargs are not used here.
    if cfg is None:
        module_name, class_name = env_cfg_entry_point.split(":")
        module = importlib.import_module(module_name)
        cfg = getattr(module, class_name)()
    return ManagerBasedEnv(cfg=cfg)


gym.register(
    id="Isaac-Data-Collection-OpenArm-Bi-v0",
    entry_point=f"{__name__}:make_manager_based_env",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.teleop_env_cfg:OpenArmDataCollectionEnvCfg",
    },
)

gym.register(
    id="Isaac-Data-Collection-OpenArm-Bi-Play-v0",
    entry_point=f"{__name__}:make_manager_based_env",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.teleop_env_cfg:OpenArmDataCollectionEnvCfg_PLAY",
    },
)
