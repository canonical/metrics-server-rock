# Metrics Server FIPS Compliance

For comprehensive information about FIPS 140-3 compliance in Canonical Kubernetes, including how ROCKs are built with FIPS support, please refer to the [k8s-snap FIPS documentation](https://github.com/canonical/k8s-snap/blob/main/docs/dev/fips.md).

> **Note:** As of now, pebble is not built in a FIPS-compliant way. This document will be updated once it is.

Metrics Server's cryptographic usage includes:

- **TLS Communication**: Secure communication with the Kubernetes API server
- **Certificate Validation**: Webhook server certificate validation
- **API Authentication**: Certificate-based authentication with the API server
