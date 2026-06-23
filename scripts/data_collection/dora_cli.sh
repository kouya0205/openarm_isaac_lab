#!/usr/bin/env bash
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

# Resolve Python/pip and the dora CLI for Isaac Lab Docker and local installs.

resolve_python() {
  local name candidate pip_path

  for name in python python3; do
    if command -v "$name" >/dev/null 2>&1; then
      command -v "$name"
      return 0
    fi
  done

  for name in pip pip3; do
    if command -v "$name" >/dev/null 2>&1; then
      pip_path="$(command -v "$name")"
      for candidate in python3 python; do
        candidate="$(dirname "$pip_path")/$candidate"
        if [[ -x "$candidate" ]]; then
          printf '%s\n' "$candidate"
          return 0
        fi
      done
    fi
  done

  for candidate in \
    /workspace/isaaclab/_isaac_sim/kit/python/bin/python3 \
    "${ISAACLAB_PATH:-}/_isaac_sim/kit/python/bin/python3"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  echo "Python interpreter not found (tried python, python3, pip sibling, Isaac Lab paths)." >&2
  return 1
}

setup_dora_path() {
  local py bin_dir

  for bin_dir in \
    /workspace/isaaclab/_isaac_sim/kit/python/bin \
    "${ISAACLAB_PATH:-}/_isaac_sim/kit/python/bin"; do
    if [[ -n "$bin_dir" && -d "$bin_dir" ]]; then
      PATH="$bin_dir:$PATH"
    fi
  done

  if py="$(resolve_python 2>/dev/null)"; then
    bin_dir="$(dirname "$py")"
    if [[ -d "$bin_dir" ]]; then
      PATH="$bin_dir:$PATH"
    fi
  fi

  export PATH
}

resolve_dora_cmd() {
  if command -v dora >/dev/null 2>&1; then
    command -v dora
    return 0
  fi

  local py dora_bin pip_bin_dir

  for dora_bin in \
    /workspace/isaaclab/_isaac_sim/kit/python/bin/dora \
    "${ISAACLAB_PATH:-}/_isaac_sim/kit/python/bin/dora"; do
    if [[ -n "$dora_bin" && -x "$dora_bin" ]]; then
      printf '%s\n' "$dora_bin"
      return 0
    fi
  done

  py="$(resolve_python)" || return 1
  dora_bin="$("$py" -c 'import os, sys; print(os.path.join(sys.prefix, "bin", "dora"))')"
  if [[ -x "$dora_bin" ]]; then
    printf '%s\n' "$dora_bin"
    return 0
  fi

  pip_bin_dir="$(dirname "$py")"
  if [[ -x "$pip_bin_dir/dora" ]]; then
    printf '%s\n' "$pip_bin_dir/dora"
    return 0
  fi

  echo "dora CLI not found. Install with: pip install -e nodes/dora-openarm-isaac" >&2
  echo "Then ensure this directory is on PATH:" >&2
  echo "  $pip_bin_dir" >&2
  return 1
}

install_dora_nodes() {
  local profile="$1"
  local py node_dir
  local -a node_dirs=()

  py="$(resolve_python)" || return 1

  case "$profile" in
    dummy)
      node_dirs=(
        nodes/dora-openarm-data-collection-ui
        nodes/dora-openarm-quitter
        nodes/dora-openarm-dummy-ker
        nodes/dora-openarm-dataset-recorder
        nodes/dora-openarm-isaac
      )
      ;;
    vr)
      node_dirs=(
        nodes/dora-openarm-data-collection-ui
        nodes/dora-openarm-quitter
        nodes/dora-openarm-dataset-recorder
        nodes/dora-openarm-vr
        nodes/dora-openarm-kinematics
        nodes/dora-openarm-isaac
      )
      ;;
    *)
      echo "Unknown profile: $profile (expected dummy or vr)" >&2
      return 1
      ;;
  esac

  echo "[install] Installing dora nodes with: $py"
  for node_dir in "${node_dirs[@]}"; do
    if [[ ! -d "$node_dir" ]]; then
      echo "Missing node directory: $node_dir (run git submodule update --init --recursive)" >&2
      return 1
    fi
    echo "[install] pip install -e $node_dir"
    "$py" -m pip install -e "$node_dir"
  done
}
