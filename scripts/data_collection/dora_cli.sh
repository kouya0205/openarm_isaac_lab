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

# Resolve the dora CLI executable.
# Isaac Sim Docker installs console scripts under sys.prefix/bin, which is often
# not on PATH even after ``pip install dora-rs-cli``.

resolve_dora_cmd() {
  if command -v dora >/dev/null 2>&1; then
    command -v dora
    return 0
  fi

  local dora_bin
  dora_bin="$(python -c 'import os, sys; print(os.path.join(sys.prefix, "bin", "dora"))')"
  if [[ -x "$dora_bin" ]]; then
    printf '%s\n' "$dora_bin"
    return 0
  fi

  echo "dora CLI not found. Install with: pip install -e nodes/dora-openarm-isaac" >&2
  echo "If already installed, add Python scripts to PATH, e.g.:" >&2
  echo "  export PATH=\"\$(python -c 'import os, sys; print(os.path.join(sys.prefix, \"bin\"))'):\$PATH\"" >&2
  return 1
}
