# ansible-wireguard-openwisp

[![Build Status](https://github.com/openwisp/ansible-wireguard-openwisp/workflows/Ansible%20WireGuard%20OpenWISP%20CI%20Build/badge.svg?branch=main)](https://github.com/openwisp/ansible-wireguard-openwisp/actions?query=Ansible+WireGuard+OpenWISP+CI+Build)

[![Gitter](https://img.shields.io/gitter/room/nwjs/nw.js.svg?style=flat-square)](https://gitter.im/openwisp/general)

Ansible role that installs WireGuard and management scripts for OpenWISP.
Once installed and configured correctly with [OpenWISP](https://github.com/openwisp/openwisp-controller/tree/1.0.x#how-to-setup-wireguard-tunnels),
WireGuard peers are managed automatically by OpenWISP without the need of
manual intervention. It also configures scripts to allow OpenWISP manage
[VXLAN over WireGuard](https://github.com/openwisp/openwisp-controller/tree/1.0.x#how-to-setup-vxlan-over-wireguard-tunnels) tunnels.

Tested on **Debian**, **Ubuntu** and **CentOS**.

**NOTE**: it is highly suggested to use this procedure on clean virtual machines or linux containers.

**Minimum ansible version supported**: 2.10.

Installing this role
-----------------

For the sake of simplicity, the easiest thing is to install this role **on your local machine**
via `ansible-galaxy`:

```
ansible-galaxy install git+https://github.com/openwisp/ansible-wireguard-openwisp.git
```

**NOTE:** This role **will not configure forwarding packets nor add static or dynamic routes** on your server.

Since the exact way in which packets can be routed can vary depending on different factors and needs which can differ greatly from organization to organization, it's left out to the user to configure it according to their needs.
[We may add a default routing/forwarding configuration in the future once we have more usage data, if you're interested in this, please let us know](https://github.com/openwisp/ansible-wireguard-openwisp/issues/8).

Role variables
==============

This role has many variables values that can be changed to best suit
your needs.

Below are listed all the variables you can customize (you may also want to take a look at
[the default values of these variables](https://github.com/openwisp/ansible-wireguard-openwisp/blob/main/defaults/main.yml)).

```yaml
- hosts: openwisp2_wireguard
  become: "{{ become | default('yes') }}"
  roles:
    - ansible-wireguard-openwisp
  vars:
    # Directory where to install upgrader scripts
    openwisp2_wireguard_directory: "{{ openwisp2_path }}/wireguard"
    # Allows to download VPN configuration by using "insecure" SSL connections.
    # It is recommended to be left as false.
    openwisp2_wireguard_curl_insecure: false
    # URL of OpenWISP Installation
    openwisp2_wireguard_controller_url: "https://openwisp.yourdomain.com"
    # UUID of the VPN generated after creating VPN server object in OpenWISP
    openwisp2_wireguard_vpn_uuid: "paste-vpn-uuid-here"
    # Key of the VPN generated after creating VPN server object in OpenWISP
    openwisp2_wireguard_vpn_key: "paste_vpn-key-here"
    # Flask endpoint to be used for triggering updates
    openwisp2_wireguard_flask_endpoint: "/trigger-update"
    # Update point authorization key
    openwisp2_wireguard_flask_key: "paste-endpoint-auth-token"
    # Port where Flask endpoint is run
    openwisp2_wireguard_flask_port: 8081
    # Host where Flask endpoint is run
    openwisp2_wireguard_flask_host: 0.0.0.0

    # specify path to a valid SSL certificate and key
    # (a self-signed SSL cert will be generated if omitted)
    openwisp2_ssl_cert: "/opt/openwisp2/ssl/server.crt"
    openwisp2_ssl_key: "/opt/openwisp2/ssl/server.key"
    # customize the self-signed SSL certificate info if needed
    openwisp2_ssl_country: "US"
    openwisp2_ssl_state: "California"
    openwisp2_ssl_locality: "San Francisco"
    openwisp2_ssl_organization: "IT dep."

    # by default python3 is used, if may need to set this to python2.7 for older systems
    openwisp2_python: python2.7
    # customize the app_path
    openwisp2_path: /opt/openwisp2
    # virtualenv command for your remote distribution, usually set automcatically
    virtualenv_command: "virtualenv"
```

Automatic SSL certificate
-------------------------

By default the playbook creates a self-signed (untrusted) SSL certificate for
the VPN endpoint. If you keep the untrusted certificate, you will also need to
disable SSL verification on OpenWISP, although we advice against using this
kind of setup in a production environment. You can
install your own trusted certificate by following steps in this section.

The first thing you have to do is to setup a valid domain for your wireguard
VPN, this means your inventory file (hosts) should look like the following:

```
[openwisp2_wireguard]
wireguard.yourdomain.com
```

You must be able to add a DNS record for `wireguard.yourdomain.com`, you cannot
use an ip address in place of `openwisp2.yourdomain.com`.

Once your domain is set up and the DNS record is propagated, proceed by
installing the ansible role [geerlingguy.certbot](https://galaxy.ansible.com/geerlingguy/certbot/)

```
ansible-galaxy install geerlingguy.certbot
```

Then proceed to edit your playbook.yml so that it will look similar to the
following example:

```yaml
- hosts: openwisp2_wireguard
  become: "{{ become | default('yes') }}"
  roles:
    - geerlingguy.certbot
    - ansible-wireguard-openwisp
  vars:
    openwisp2_wireguard_controller_url: "https://openwisp.yourdomain.com"
    openwisp2_wireguard_vpn_uuid: "paste-vpn-uuid-here"
    openwisp2_wireguard_vpn_key: "paste_vpn-key-here"
    openwisp2_wireguard_flask_key: "paste-endpoint-auth-token"

    # SSL certificates
    openwisp2_ssl_cert: "/etc/letsencrypt/live/{{ ansible_fqdn }}/fullchain.pem"
    openwisp2_ssl_key: "/etc/letsencrypt/live/{{ ansible_fqdn }}/privkey.pem"

    # certbot configuration
    certbot_auto_renew_user: "privileged-users-to-renew-certs"
    certbot_auto_renew_minute: "20"
    certbot_auto_renew_hour: "5"
    certbot_create_if_missing: true
    certbot_create_standalone_stop_services: []
    certbot_certs:
      - email: "paste-your-email"
        domains:
          - wireguard.yourdomain.com
```

Read the [documentation of `geerlingguy.certbot`](https://github.com/geerlingguy/ansible-role-certbot#readme)
to learn more about configuration of certbot role.

How to run tests
----------------

If you want to contribute to `ansible-wireguard-openwisp` you should run tests
in your development environment to ensure your changes are not breaking anything.

To do that, proceed with the following steps:

**Step 1**: Clone `ansible-wireguard-openwisp`

Clone repository by:

```
git clone https://github.com/<your_fork>/ansible-wireguard-openwisp.git
```

**Step 2**: Install docker

If you haven't installed docker yet, you need to install it (example for linux debian/ubuntu systems):

```
sudo apt-get install docker.io
```

**Step 3**: Install molecule and dependencies

```
pip install molecule[docker,ansible] yamllint ansible-lint docker
```

**Step 4**: Download docker images

```
docker pull geerlingguy/docker-ubuntu2004-ansible:latest
docker pull geerlingguy/docker-ubuntu1804-ansible:latest
docker pull geerlingguy/docker-debian10-ansible:latest
docker pull geerlingguy/docker-centos7-ansible:latest
docker pull geerlingguy/docker-centos8-ansible:latest
```

**Step 5**: Run molecule test

```
molecule test -s local
```

If you don't get any error message it means that the tests ran successfully without errors.

**ProTip:** Use `molecule test -s local --destroy=never` to speed up subsequent test runs.

Contributing
============

Please read the [OpenWISP contributing guidelines](http://openwisp.io/docs/developer/contributing.html).

License
=======

See [LICENSE](https://github.com/openwisp/openwisp-notifications/blob/master/LICENSE).

Support
=======

See [OpenWISP Support Channels](http://openwisp.org/support.html).
