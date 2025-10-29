#
# Copyright 2025 Canonical, Ltd.
#
import shlex
from pathlib import Path

import pytest
import yaml
from k8s_test_harness.util import docker_util, env_util

TEST_PATH = Path(__file__)
REPO_PATH = TEST_PATH.parent.parent.parent
IMAGE_BASE = "ghcr.io/canonical/metrics-server:"


def _image_versions():
    all_rockcrafts = REPO_PATH.glob("**/rockcraft.yaml")
    yamls = [yaml.safe_load(rock.read_bytes()) for rock in all_rockcrafts]
    return [rock["version"] for rock in yamls]


@pytest.mark.parametrize("image_version", _image_versions())
@pytest.mark.parametrize(
    "executable, check_version",
    [("/metrics-server --version", True), ("/bin/pebble version", False)],
)
def test_sanity(image_version, executable, check_version):
    try:
        rock = env_util.get_build_meta_info_for_rock_version(
            "metrics-server", image_version, "amd64"
        )
        image = rock.image
    except OSError:
        image = f"{IMAGE_BASE}{image_version}"
    entrypoint = shlex.split(executable)

    process = docker_util.run_in_docker(image, entrypoint, check_exit_code=False)
    assert (
        process.returncode == 0
    ), f"Failed to run {entrypoint} in image {image}, stderr: {process.stderr}"
    if check_version:
        assert image_version in process.stdout
