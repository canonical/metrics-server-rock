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


def is_fips_rock(image_version):
    return "fips" in (REPO_PATH / image_version / "rockcraft.yaml").read_text().lower()


def _image_versions():
    all_rockcrafts = REPO_PATH.glob("**/rockcraft.yaml")
    yamls = [yaml.safe_load(rock.read_bytes()) for rock in all_rockcrafts]
    return [rock["version"] for rock in yamls]


def resolve_image(image_version):
    try:
        rock = env_util.get_build_meta_info_for_rock_version(
            "metrics-server", image_version, "amd64"
        )
        return rock.image
    except OSError:
        return f"{IMAGE_BASE}{image_version}"


def _run_entrypoint_and_assert(image, entrypoint, expect_stdout_contains=None):
    entry = shlex.split(entrypoint) if isinstance(entrypoint, str) else entrypoint
    process = docker_util.run_in_docker(image, entry, check_exit_code=False)
    assert (
        process.returncode == 0
    ), f"Failed to run {entry} in image {image}, stderr: {process.stderr}"
    if expect_stdout_contains:
        assert (
            expect_stdout_contains in process.stdout
        ), f"Expected '{expect_stdout_contains}' in stdout for {entry} in image {image}, stdout: {process.stdout}"


@pytest.mark.parametrize("image_version", _image_versions())
def test_metrics_server_executable(image_version):
    image = resolve_image(image_version)
    _run_entrypoint_and_assert(
        image, "/metrics-server --version", expect_stdout_contains=image_version
    )


@pytest.mark.parametrize("image_version", _image_versions())
def test_pebble_executable(image_version):
    image = resolve_image(image_version)
    _run_entrypoint_and_assert(
        image, "/bin/pebble version", expect_stdout_contains="v1.14.0"
    )


@pytest.mark.parametrize("GOFIPS", [0, 1], ids=lambda v: f"GOFIPS={v}")
@pytest.mark.parametrize("image_version", _image_versions())
def test_fips(image_version, GOFIPS):
    image = resolve_image(image_version)
    entrypoint = shlex.split("/metrics-server --version")

    docker_env = ["-e", f"GOFIPS={GOFIPS}"]
    process = docker_util.run_in_docker(
        image, entrypoint, check_exit_code=False, docker_args=docker_env
    )

    if is_fips_rock(image_version):
        # fipsed ROCKs should fail if GOFIPS set on a non-fips system
        # since the modified Go toolchain checks for a FIPS-capable crypto backend.
        expected_returncode = 2 if GOFIPS == 1 else 0
        expected_error = "FIPS" if GOFIPS == 1 else ""
    else:
        # non-FIPS ROCKs should not care about GOFIPS setting and always succeed
        expected_returncode = 0
        expected_error = ""

    assert (
        process.returncode == expected_returncode
    ), f"Return code mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
    assert (
        expected_error in process.stderr
    ), f"Error message mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
