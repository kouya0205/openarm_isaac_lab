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

# Initialize git submodules required by a data-collection profile.
# Normally satisfied by ``git clone --recursive``; this is a fallback.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PROFILE="${1:?Usage: init_submodules.sh dummy|vr}"

DUMMY_PATHS=(
  nodes/dora-openarm-data-collection-ui
  nodes/dora-openarm-quitter
  nodes/dora-openarm-dummy-ker
  nodes/dora-openarm-dataset-recorder
)

VR_PATHS=(
  nodes/dora-openarm-data-collection-ui
  nodes/dora-openarm-quitter
  nodes/dora-openarm-dataset-recorder
  nodes/dora-openarm-vr
  nodes/dora-openarm-kinematics
)

case "$PROFILE" in
  dummy) PATHS=("${DUMMY_PATHS[@]}") ;;
  vr) PATHS=("${VR_PATHS[@]}") ;;
  *)
    echo "Unknown profile: $PROFILE (expected dummy or vr)" >&2
    exit 1
    ;;
esac

git submodule update --init --recursive "${PATHS[@]}"
