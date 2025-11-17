## Overview
This document provides an analysis of metric server's cryptographic implementation
with respect to FIPS 140 compliance requirements.

> **Note:** As of now, pebble is not built in a FIPS-compliant way. This document will be updated once it is.

## FIPS Compliance Status

Metrics-server uses both standard Go `crypto` and the extended `https://pkg.go.dev/golang.org/x/crypto` modules. To address the FIPS compliance for the standard package, the following steps are required:

1. **Go Toolchain**: Must use the modified [Go toolchain from Microsoft](https://github.com/microsoft/go/blob/microsoft/release-branch.go1.24/eng/doc/fips/README.md) that links against FIPS-validated cryptographic modules.
2. **OpenSSL**: Must link against a FIPS-validated OpenSSL implementation.

**NOTE**: This ROCK is bundled with a FIPS-validated OpenSSL library which is described in the ROCK manifest (see [this discourse post]).
```yaml
...
parts:
  openssl:
    plugin: nil
    stage-packages:
      - openssl-fips-module-3
      - openssl
...
```

For the extended module, enduring the non-approved algorithms are not executed would suffice.  

## Manual build and test

To manually build the fips-compliant rock image you need an Ubuntu Pro token. Once obtained, you can follow these intructions:

1. **Prerequisites**:
   - `rockcraft` version that contains the pro feature (see [this discourse post]).

2. **Build Command**:

   ```bash
   sudo rockcraft pack --pro=fips-updates
   ```

<!-- LINKS -->

[this discourse post]: https://discourse.ubuntu.com/t/build-rocks-with-ubuntu-pro-services/57578
