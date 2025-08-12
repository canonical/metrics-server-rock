## Overview
This document provides an analysis of metric server's cryptographic implementation
with respect to FIPS 140 compliance requirements.

## FIPS Compliance Status

Metrics-server uses both standard Go `crypto` and the extended `https://pkg.go.dev/golang.org/x/crypto` modules. To address the FIPS compliance for the standard package, the following steps are required:

1. **Go Toolchain**: Must use the modified [Go toolchain from Microsoft](https://github.com/microsoft/go/blob/microsoft/release-branch.go1.24/eng/doc/fips/README.md) that links against FIPS-validated cryptographic modules.
2. **OpenSSL**: Must link against a FIPS-validated OpenSSL implementation, e.g. from `core22/fips`.
3. **Build Environment**: Must be built on an Ubuntu Pro machine with FIPS updates enabled, see below.

For the extended module, enduring the non-approved algorithms are not executed would suffice.  

## Manual build and test

To manually build the fips-compliant rock image you need an Ubuntu Pro token. Once obtained, you can follow these intructions:

- Install multipass on a machine with enabled virtualization capabilities:

```
sudo snap install multipass
```

- Launch a builder instance with an attached Ubuntu Pro account:

```
cat <<EOF | multipass launch --name rock-builder --cloud-init - --cpus 4 --disk 20GB --memory 8GB 22.04
package_update: true
package_upgrade: true
packages:
- ubuntu-advantage-tools
runcmd:
- pro attach <UBUNTU_PRO_TOKEN> --no-auto-enable
- reboot
EOF
```

- Install rockcraft from the `edge/pro-sources` channel

```
multipass exec rock-builder -- sudo snap install rockcraft --channel=edge/pro-sources --classic

```
- Initialize `lxd` on the machine 
```

multipass exec rock-builder -- lxd init --auto

```

- Switch to the directory where you `rockcraft.yaml` file is located and mount the directory on Multipass instance

```
multipass mount . rock-builder:/home/ubuntu/rock
```

- Pack the rock image with the `fips-updates` service enabled on both the build environment and the rock

```
multipass exec rock-builder -d /home/ubuntu/rock -- sudo rockcraft pack --pro=fips-updates
```