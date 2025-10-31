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


@pytest.mark.parametrize("image_version", _image_versions())
@pytest.mark.parametrize(
    "executable, check_version",
    [("/metrics-server --version", True), ("/bin/pebble version", False)],
    ids=["metrics-server", "pebble"],
)
def test_executables(image_version, executable, check_version, GOFIPS):
    image = resolve_image(image_version)
    entrypoint = shlex.split(executable)

    process = docker_util.run_in_docker(image, entrypoint, check_exit_code=False)
    assert (
        process.returncode == 0
    ), f"Failed to run {entrypoint} in image {image}, stderr: {process.stderr}"
    if check_version:
        assert image_version in process.stdout


@pytest.mark.parametrize("GOFIPS", [0, 1], ids=lambda v: f"GOFIPS={v}")
@pytest.mark.parametrize("image_version", _image_versions())
@pytest.mark.parametrize(
    "executable",
    ["/metrics-server --version"],
    ids=["metrics-server"],
)
def test_fips(image_version, executable, GOFIPS):
    image = resolve_image(image_version)
    entrypoint = shlex.split(executable)

    docker_env = ["-e", f"GOFIPS={GOFIPS}"]
    process = docker_util.run_in_docker(
        image, entrypoint, check_exit_code=False, docker_args=docker_env
    )

    if is_fips_rock(image_version):
        # fipsed ROCKs should fail if GOFIPS set on a non-fips system
        # since the modified Go toolchain checks for a FIPS-capable crypto backend.
        expected_returncode = 1 if GOFIPS == 1 else 1
        expected_error = (
            "no supported crypto backend is enabled"
            if GOFIPS == 1
            else ""
        )
    else:
        # non-FIPS ROCKs should not care about GOFIPS setting and always succeed
        expected_returncode = 0
        expected_error = ""

    assert process.returncode == expected_returncode, f"Return code mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
    assert expected_error in process.stderr, f"Error message mismatch for {entrypoint} in image {image}, stderr: {process.stderr}"
