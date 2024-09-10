# Changelog

## Version 1.2.0 [2024-09-10]

### Changes

**Dependencies:**

- Bumped `Flask~=3.0.3`
- Bumped `uwsgi~=2.0.26`
- Bumped `Werkzeug~=3.0.3`
- Added support for Debian 12
- Added support for Ubuntu 24.04
- Dropped support for CentOS 7 and 8

## Version 1.1.0 [2024-05-18]

### Features

- Allowed adding multiple peers to VXLAN tunnel
- Added more logging capabilities to the Flask app
  and `update_wireguard.sh` script

### Fixes

- Added "Werkzeug>=2.0, <3.0" in Python dependencies
- Added support for Ubuntu 22.04, Dropped Debian 10 and Ubuntu 18.04

## Version 1.0.2 [2023-03-01]

### Fixes

- Removed deprecated ansible-command args

## Version 1.0.1 [2022-08-31]

### Changes

- Upgraded Flask to `2.0.x`

## Version 1.0.0 [2022-04-29]

### Features

- Installs scripts for OpenWISP to automate the management of
  WireGuard peers and VXLAN tunnels.
