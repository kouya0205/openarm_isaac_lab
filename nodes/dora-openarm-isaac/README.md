# dora-openarm-isaac

Isaac Sim / Isaac Lab dora node for OpenArm bimanual teleoperation data collection.

Drop-in replacement for `dora-openarm-mujoco` in a dora dataflow. Uses the Phase 1
`Isaac-Data-Collection-OpenArm-Bi-v0` environment from this repository.

## Prerequisites

Linux with Isaac Sim 5.1.0 / Isaac Lab 2.3.0 and the `openarm` package installed:

```bash
cd openarm_isaac_lab
python -m pip install -e source/openarm
pip install -e nodes/dora-openarm-isaac
```

## Standalone smoke test

Clone with submodules (``git clone --recursive``), then from the repository root:

```bash
./scripts/data_collection/run_dummy.sh
```

## Dataflow I/O

Same contract as `dora-openarm-mujoco`:

| Direction | ID | Type |
|-----------|-----|------|
| in | `position_left`, `position_right` | float32[8] |
| in | `pose_left`, `pose_right` | float32[7] (optional) |
| out | `status` | string |
| out | `arm_left_observation`, `arm_right_observation` | float32[8] |
| out | `camera_wrist_*`, `camera_head_*`, `camera_ceiling` | JPEG uint8 |

## CLI

```bash
dora-openarm-isaac --headless --enable_cameras --render
```

| Flag | Description |
|------|-------------|
| `--task` | Gym task id (default: headless data-collection env) |
| `--render` | Publish JPEG camera outputs at ~30 Hz |
| `--headless` | Run without GUI (AppLauncher) |
| `--enable_cameras` | Required with `--render` for offscreen cameras |
