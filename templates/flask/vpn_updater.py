import subprocess

from flask import Flask, Response, request

app = Flask(__name__)

KEY = '{{ openwisp2_wireguard_flask_key }}'
UPDATER_SCRIPTS = [
    '{{ openwisp2_wireguard_path }}/update_wireguard.sh check_config',
]


def _exec_command(command):
    process = subprocess.Popen(
        command.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    stdout, stderr = process.communicate()
    exit_code = process.wait(timeout=10)
    if exit_code != 0:
        raise subprocess.SubprocessError()


@app.route('{{ openwisp2_wireguard_flask_endpoint }}', methods=['POST'])
def update_vpn_config():
    if request.args.get('key') != KEY:
        return Response(status=403)
    for script in UPDATER_SCRIPTS:
        try:
            _exec_command(script)
        except subprocess.SubprocessError:
            return Response(status=500)
    return Response(status=200)


if __name__ == '__main__':
    app.run()
