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

"""Smoke test for the bimanual data-collection environment (Phase 1).

Run on Linux with Isaac Sim / Isaac Lab installed:

    python scripts/teleoperation/verify_data_collection_env.py \
      --task Isaac-Data-Collection-OpenArm-Bi-Play-v0

Use ``--headless`` for servers without a display.
"""

"""Launch Isaac Sim Simulator first."""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Verify OpenArm data-collection environment.")
parser.add_argument(
    "--task",
    type=str,
    default="Isaac-Data-Collection-OpenArm-Bi-Play-v0",
    help="Registered Gym task id.",
)
parser.add_argument("--num_steps", type=int, default=120, help="Simulation steps to run.")
parser.add_argument(
    "--output_dir",
    type=str,
    default=None,
    help="Optional directory to save one RGB frame per camera after the run.",
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Camera sensors require the offscreen rendering pipeline.
args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import os
import traceback

import gymnasium as gym
import numpy as np
import torch

import openarm.tasks  # noqa: F401
from isaaclab.envs import ManagerBasedEnv
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg

from openarm.tasks.manager_based.openarm_manipulation.bimanual.data_collection.joint_utils import (
    DORA_CAMERA_NAMES,
)


def _print_observation_summary(obs: dict) -> None:
    recording = obs.get("recording", obs)
    if not isinstance(recording, dict):
        print(f"  recording: type={type(recording)}, shape={getattr(recording, 'shape', None)}")
        return
    for key, value in recording.items():
        if isinstance(value, torch.Tensor):
            print(f"  {key}: shape={tuple(value.shape)}, dtype={value.dtype}")
        else:
            print(f"  {key}: type={type(value)}")


def _save_camera_samples(obs: dict, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    recording = obs.get("recording", obs)
    saved = 0
    for cam_name in DORA_CAMERA_NAMES:
        if cam_name not in recording:
            continue
        rgb = recording[cam_name]
        if isinstance(rgb, torch.Tensor):
            rgb = rgb[0].detach().cpu().numpy()
        if rgb.dtype != np.uint8:
            rgb = np.clip(rgb * 255.0 if rgb.max() <= 1.0 else rgb, 0, 255).astype(np.uint8)
        try:
            from PIL import Image
        except ImportError as exc:
            raise ImportError("Install pillow to use --output_dir (pip install pillow).") from exc
        Image.fromarray(rgb).save(os.path.join(output_dir, f"{cam_name}.png"))
        saved += 1
    print(f"Saved {saved} camera images to {output_dir}")


def _create_env(task: str) -> ManagerBasedEnv:
    env_cfg = parse_env_cfg(task, device=args_cli.device, num_envs=1)
    return gym.make(task, cfg=env_cfg)


def main() -> None:
    env = _create_env(args_cli.task)

    print(f"Task: {args_cli.task}")

    obs, _ = env.reset()
    print(f"Action shape: {tuple(env.action_manager.action.shape)}")
    print("Initial recording observations:")
    _print_observation_summary(obs)

    zero_action = torch.zeros_like(env.action_manager.action)
    for step in range(args_cli.num_steps):
        obs, _ = env.step(zero_action)
        if step % 30 == 0:
            print(f"step {step}: left qpos[0]={obs['recording']['left_arm_qpos'][0, 0].item():.4f}")

    print("Final recording observations:")
    _print_observation_summary(obs)

    if args_cli.output_dir is not None:
        _save_camera_samples(obs, args_cli.output_dir)

    env.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
    finally:
        simulation_app.close()
