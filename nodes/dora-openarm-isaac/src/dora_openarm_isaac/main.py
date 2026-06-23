# Copyright 2026 Enactic, Inc.
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

"""
dora-openarm-isaac — Isaac Sim simulation node for OpenArm bimanual data collection
====================================================================================

This dora node replaces ``dora-openarm-mujoco`` in a dataflow. It loads the
Phase 1 bimanual data-collection environment from ``openarm_isaac_lab`` and
publishes the same I/O contract (joint qpos + five JPEG cameras).

Prerequisites
-------------
Run inside an Isaac Lab environment with ``openarm`` installed::

    cd openarm_isaac_lab
    python -m pip install -e source/openarm
    pip install -e nodes/dora-openarm-isaac

Inputs
------
position_right / position_left : float32[8] or struct{new_position: float32[8], ...}
    Target joint positions for each arm (joints 1–7 + gripper finger joint).

pose_right / pose_left : float32[7]
    VR controller pose. Accepted for dataflow compatibility; ignored unless
    ``--debug-frames`` is added in a future phase.

Outputs
-------
status : string["ready"]
    Published once on startup.

arm_right_observation / arm_left_observation : float32[8]
    Observed joint positions published after each incoming position command.

camera_* : uint8[N]
    JPEG-encoded frames at ~30 Hz when ``--render`` is set.
    Each output carries ``metadata={"encoding": "jpeg"}``.

CLI arguments (AppLauncher + node options)
------------------------------------------
--task TASK
    Registered data-collection task id (default: headless variant).

--render
    Enable camera rendering and publish JPEG frames.

--headless / --enable_cameras
    Standard Isaac Lab AppLauncher flags (set ``--enable_cameras`` with ``--render``).
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
import time
import traceback

import cv2
import numpy as np
import pyarrow as pa
from isaaclab.app import AppLauncher

# Maps dora input IDs to arm sides for position events.
_ARM_INPUT_SIDES = {"position_right": "right", "position_left": "left"}

# Camera rendering rate (matches dora-openarm-mujoco).
_CAM_HZ = 30
_CAM_DT = 1.0 / _CAM_HZ
_JPEG_QUALITY = 90

_DEFAULT_TASK = "Isaac-Data-Collection-OpenArm-Bi-v0"


def _parse_launcher_args() -> tuple[argparse.Namespace, AppLauncher]:
    """Parse AppLauncher args before importing Isaac Lab env modules."""
    parser = argparse.ArgumentParser(
        description="Isaac Sim dora node for OpenArm bimanual data collection",
    )
    parser.add_argument(
        "--task",
        type=str,
        default=_DEFAULT_TASK,
        help="Registered data-collection task id.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Enable offscreen camera rendering and publish JPEG frames.",
    )
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.render:
        args.enable_cameras = True
    app_launcher = AppLauncher(args)
    return args, app_launcher


def _extract_float32_8(value) -> np.ndarray | None:
    """Parse dora position payload into float32[8]."""
    if isinstance(value, pa.StructArray):
        value = value.field("new_position")
    values = np.asarray(value, dtype=np.float32)
    if values.shape != (8,):
        return None
    return values


def _rgb_to_jpeg_bytes(rgb: np.ndarray) -> bytes | None:
    """Encode an RGB uint8 frame as JPEG bytes."""
    if rgb.dtype != np.uint8:
        if rgb.max() <= 1.0:
            rgb = np.clip(rgb * 255.0, 0, 255)
        rgb = rgb.astype(np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY])
    if not ok:
        return None
    return buf.tobytes()


class _SharedArmState:
    """Thread-safe latest joint targets and pending observation flags."""

    def __init__(self, left: np.ndarray, right: np.ndarray):
        self._lock = threading.Lock()
        self.left = left.copy()
        self.right = right.copy()
        self.pending_obs: set[str] = set()

    def update_target(self, side: str, values: np.ndarray) -> None:
        with self._lock:
            if side == "left":
                self.left = values.copy()
            else:
                self.right = values.copy()
            self.pending_obs.add(side)

    def snapshot(self) -> tuple[np.ndarray, np.ndarray, set[str]]:
        with self._lock:
            pending = set(self.pending_obs)
            self.pending_obs.clear()
            return self.left.copy(), self.right.copy(), pending


def _run_dora(
    node,
    state: _SharedArmState,
    stop_event: threading.Event,
) -> None:
    """Background dora event loop: receive joint targets, ignore VR poses for now."""
    print("[dora] Event loop started.")
    try:
        for event in node:
            if stop_event.is_set():
                break
            if event["type"] != "INPUT":
                continue

            eid = event["id"]
            if eid in _ARM_INPUT_SIDES:
                values = _extract_float32_8(event["value"])
                if values is not None:
                    state.update_target(_ARM_INPUT_SIDES[eid], values)
            elif eid in ("pose_right", "pose_left"):
                # Accepted for dataflow wiring; debug overlay is Phase 3.
                pass
    finally:
        print("[dora] Event loop ended – signalling shutdown.")
        stop_event.set()


def _publish_arm_observation(node, side: str, qpos: np.ndarray) -> None:
    node.send_output(f"arm_{side}_observation", pa.array(qpos, type=pa.float32()))


def _publish_cameras(node, recording: dict) -> None:
    from openarm.tasks.manager_based.openarm_manipulation.bimanual.data_collection.joint_utils import (
        DORA_CAMERA_NAMES,
    )

    for cam_name in DORA_CAMERA_NAMES:
        if cam_name not in recording:
            continue
        rgb = recording[cam_name]
        if hasattr(rgb, "detach"):
            rgb = rgb[0].detach().cpu().numpy()
        jpeg_bytes = _rgb_to_jpeg_bytes(rgb)
        if jpeg_bytes is None:
            continue
        node.send_output(
            cam_name,
            pa.array(np.frombuffer(jpeg_bytes, dtype=np.uint8), type=pa.uint8()),
            metadata={"encoding": "jpeg"},
        )


def _run_sim_loop(
    env,
    node,
    state: _SharedArmState,
    stop_event: threading.Event,
    *,
    render: bool,
) -> None:
    """Main Isaac Sim loop: step physics and publish observations/cameras."""
    import torch

    sim_dt = env.cfg.sim.dt
    next_cam = time.perf_counter() + _CAM_DT

    while not stop_event.is_set():
        t0 = time.perf_counter()

        left, right, pending = state.snapshot()
        action = torch.tensor(
            np.concatenate([left, right], dtype=np.float32),
            device=env.device,
            dtype=torch.float32,
        ).unsqueeze(0)
        obs, _ = env.step(action)
        recording = obs.get("recording", obs)

        if pending:
            if "left" in pending:
                q = recording["left_arm_qpos"][0].detach().cpu().numpy().astype(np.float32)
                _publish_arm_observation(node, "left", q)
            if "right" in pending:
                q = recording["right_arm_qpos"][0].detach().cpu().numpy().astype(np.float32)
                _publish_arm_observation(node, "right", q)

        if render and time.perf_counter() >= next_cam:
            _publish_cameras(node, recording)
            next_cam += _CAM_DT

        elapsed = time.perf_counter() - t0
        if elapsed < sim_dt:
            time.sleep(sim_dt - elapsed)


def main() -> None:
    args, app_launcher = _parse_launcher_args()
    simulation_app = app_launcher.app

    import dora
    import openarm.tasks  # noqa: F401

    from openarm.tasks.manager_based.openarm_manipulation.bimanual.data_collection.config import (
        create_data_collection_env,
    )

    stop_event = threading.Event()

    def _on_signal(sig, _frame):
        print(f"[main] Received signal {sig}, shutting down.")
        stop_event.set()

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    print(f"[env] Loading task: {args.task}")
    env = create_data_collection_env(args.task, device=args.device, num_envs=1)
    obs, _ = env.reset()
    recording = obs.get("recording", obs)

    left0 = recording["left_arm_qpos"][0].detach().cpu().numpy().astype(np.float32)
    right0 = recording["right_arm_qpos"][0].detach().cpu().numpy().astype(np.float32)
    state = _SharedArmState(left0, right0)

    node = dora.Node()
    node.send_output("status", pa.array(["ready"]))
    _publish_arm_observation(node, "right", right0)
    _publish_arm_observation(node, "left", left0)

    print(f"[env] Action shape: {tuple(env.action_manager.action.shape)}")
    if args.render:
        print("[camera] Rendering enabled (~30 Hz JPEG outputs).")

    dora_thread = threading.Thread(
        target=_run_dora,
        args=(node, state, stop_event),
        daemon=True,
    )
    dora_thread.start()

    try:
        _run_sim_loop(env, node, state, stop_event, render=args.render)
    finally:
        stop_event.set()
        dora_thread.join(timeout=2.0)
        env.close()
        simulation_app.close()
        print("[main] Shutdown complete.")


def cli_main() -> None:
    """Console entrypoint.

    Isaac Sim can raise during Python interpreter teardown after a clean shutdown.
    Exit explicitly so Dora observes the real result.
    """
    exit_code = 0
    try:
        main()
    except SystemExit as exc:
        if exc.code is None:
            exit_code = 0
        elif isinstance(exc.code, int):
            exit_code = exc.code
        else:
            exit_code = 1
            try:
                print(exc.code, file=sys.stderr)
            except Exception:
                pass
    except KeyboardInterrupt:
        exit_code = 130
        try:
            traceback.print_exc()
        except Exception:
            pass
    except BaseException:
        exit_code = 1
        try:
            traceback.print_exc()
        except Exception:
            pass
    finally:
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except Exception:
                pass
    os._exit(exit_code)


if __name__ == "__main__":
    cli_main()
