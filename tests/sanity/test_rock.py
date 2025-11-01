#
# Copyright 2025 Canonical, Ltd.
#
import shlex
from pathlib import Path

import pytest
from k8s_test_harness.util import docker_util, env_util, fips_util

TEST_PATH = Path(__file__)
REPO_PATH = TEST_PATH.parent.parent.parent
IMAGE_NAME = "metrics-server"
IMAGE_BASE = f"ghcr.io/canonical/{IMAGE_NAME}:"
IMAGE_ENTRYPOINT = "/metrics-server --version"


@pytest.mark.parametrize("image_version", env_util.image_versions_in_repo(REPO_PATH))
def test_executable(image_version):
    image = env_util.resolve_image(IMAGE_NAME, image_version)
    docker_util.run_entrypoint_and_assert(
        image, IMAGE_ENTRYPOINT, expect_stdout_contains=image_version
    )


@pytest.mark.parametrize("image_version", env_util.image_versions_in_repo(REPO_PATH))
def test_pebble_executable(image_version):
    image = env_util.resolve_image(IMAGE_NAME, image_version)
    docker_util.run_entrypoint_and_assert(
        image, "/bin/pebble version", expect_stdout_contains="v1.14.0"
    )


@pytest.mark.parametrize("GOFIPS", [0, 1], ids=lambda v: f"GOFIPS={v}")
@pytest.mark.parametrize("image_version", env_util.image_versions_in_repo(REPO_PATH))
def test_fips(image_version, GOFIPS):
    image = env_util.resolve_image(IMAGE_NAME, image_version)
    entrypoint = shlex.split(IMAGE_ENTRYPOINT)

    docker_env = ["-e", f"GOFIPS={GOFIPS}"]
    process = docker_util.run_in_docker(
        image, entrypoint, check_exit_code=False, docker_args=docker_env
    )

    rockcraft_yaml = (REPO_PATH / image_version / "rockcraft.yaml").read_text().lower()
    expected_returncode, expected_error = fips_util.fips_expectations(
        rockcraft_yaml, GOFIPS
    )

    assert (
        process.returncode == expected_returncode
    ), f"Return code mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
    assert (
        expected_error in process.stderr
    ), f"Error message mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
