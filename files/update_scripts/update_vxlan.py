#!/usr/bin/env python3

import json
import subprocess
import sys
import os

VXLAN_IPV4_METHOD = os.environ.get('VXLAN_IPV4_METHOD', 'link-local')
VXLAN_IPV6_METHOD = os.environ.get('VXLAN_IPV6_METHOD', 'link-local')

try:
    peer_file_path = sys.argv[1]
except IndexError:
    print('peer file must be passed as firs argument', file=sys.stderr)
    sys.exit(1)

try:
    with open(peer_file_path, 'r') as peer_file:
        contents = peer_file.read()
except FileNotFoundError as e:
    print(e, file=sys.stderr)
    sys.exit(2)

try:
    tunnels = json.loads(contents)
    assert isinstance(tunnels, list)
except Exception as e:
    print(f'Error while parsing JSON file: {e}', file=sys.stderr)
    sys.exit(3)


remote_tunnels = {}

for tunnel in tunnels:
    try:
        remote_tunnels[f'vxlan-vxlan{tunnel["vni"]}'].append(tunnel)
    except KeyError:
        remote_tunnels[f'vxlan-vxlan{tunnel["vni"]}'] = [tunnel]


class Base(object):
    @classmethod
    def _exec_command(cls, command):
        process = subprocess.Popen(
            command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if stderr:
            raise ValueError(stderr)
        return stdout.decode('utf8').strip()


class Nmcli(Base):
    @classmethod
    def list_connections(cls, type=None):
        output = cls._exec_command('nmcli connection show')
        lines = output.split('\n')
        connections = []
        for line in lines[1:]:
            parts = line.split()
            connection = {
                'name': parts[0].strip(),
                'uuid': parts[1].strip(),
                'type': parts[2].strip(),
                'device': parts[3].strip(),
            }
            if not type or type and type == connection['type']:
                connections.append(connection)
        return connections

    @classmethod
    def get_connection(cls, connection):
        output = cls._exec_command(f'sudo nmcli connection show {connection}')
        data = {}
        lines = output.split('\n')
        for line in lines:
            parts = line.split()
            data[parts[0][:-1]] = parts[1]
        return data

    @classmethod
    def get_local_vxlan_tunnels(cls):
        peers = {}
        vxlan_connections = cls.list_connections(type='vxlan')
        for vxlan in vxlan_connections:
            data = cls.get_connection(vxlan['uuid'])
            peers[data['connection.id']] = {
                'remote': data['vxlan.remote'],
                'vni': int(data['vxlan.id']),
            }
        return peers

    @classmethod
    def add_connection(cls, ifname, vni, remote):
        return cls._exec_command(
            f'sudo nmcli connection add type vxlan ifname {ifname} '
            f'id {vni} remote {remote} destination-port 4789 '
            f'ipv4.method {VXLAN_IPV4_METHOD} ipv6.method {VXLAN_IPV6_METHOD}'
        )

    @classmethod
    def edit_connection(cls, connection, vni, remote):
        return cls._exec_command(
            f'sudo nmcli connection modify {connection} vxlan.id {vni} vxlan.remote {remote}'
        )

    @classmethod
    def delete_connection(cls, connection):
        return cls._exec_command(f'sudo nmcli connection delete {connection}')


class Bridge(Base):
    @classmethod
    def list_vxlan_peers(cls, interface=None):
        command = 'sudo bridge fdb show'
        if interface:
            command += f' dev {interface}'
        output = cls._exec_command(command)
        lines = output.split('\n')
        peers = []
        remote_ip_index = 2 if interface else 4
        for line in lines:
            parts = line.split()
            if parts[0].strip() != '00:00:00:00:00:00':
                continue
            peers.append(parts[remote_ip_index].strip())
        return peers

    @classmethod
    def add_vxlan_peer(cls, peer_ip, interface):
        cls._exec_command(
            f'sudo bridge fdb append to 00:00:00:00:00:00 dst {peer_ip} dev {interface}'
        )

    @classmethod
    def remove_vxlan_peer(cls, peer_ip, interface):
        cls._exec_command(
            'sudo bridge fdb del to 00:00:00:00:00:00'
            f' dst {peer_ip} dev {interface}'
        )


local_tunnels = Nmcli.get_local_vxlan_tunnels()


for connection_name in local_tunnels.keys():
    if connection_name not in remote_tunnels:
        Nmcli.delete_connection(connection_name)
        print(f'Removed {connection_name}')

for connection_name, tunnel_data in remote_tunnels.items():
    vni = tunnel_data[0]['vni']
    remote = tunnel_data[0]['remote']
    interface = tunnel_data[0].get('interface', 'vxlan')
    interface = f'{interface}{vni}'
    if connection_name not in local_tunnels:
        Nmcli.add_connection(interface, vni, remote)
        print(f'Added {connection_name}')
    elif tunnel_data == local_tunnels[connection_name]:
        print(f'Skipping {connection_name}, already up to date')
    else:
        Nmcli.edit_connection(connection_name, vni, remote)
        print(f'Updated {connection_name}')

    local_vxlan_peers = Bridge.list_vxlan_peers(interface=interface)
    remote_vxlan_peers = [remote]
    # Add peers
    for peer in tunnel_data[1:]:
        if peer['remote'] not in local_vxlan_peers:
            Bridge.add_vxlan_peer(peer['remote'], interface)
            print(f'Added {peer["remote"]} to {interface}')
        remote_vxlan_peers.append(peer['remote'])
    # Remove peers
    for peer in local_vxlan_peers:
        if peer not in remote_vxlan_peers:
            Bridge.remove_vxlan_peer(peer, interface)
            print(f'Removed {peer} from {interface}')
