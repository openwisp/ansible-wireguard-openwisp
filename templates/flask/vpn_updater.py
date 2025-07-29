import hmac
import logging
import subprocess

from flask import Flask, Response, request

app = Flask(__name__)

KEY = "{{ openwisp2_wireguard_flask_key }}"
UPDATER_SCRIPTS = [
    "{{ openwisp2_wireguard_path }}/update_wireguard.sh check_config",
]


# Configure logging
app.logger.setLevel(
    getattr(logging, "{{ openwisp2_wireguard_logging_level }}", "WARNING")
)


def _exec_command(command):
    process = subprocess.Popen(
        command.split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        universal_newlines=True,
    )
    try:
        stdout, _ = process.communicate(timeout=10)
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, _ = process.communicate()
        stdout += "\n***** Command was terminated due to timeout. *****\n"
        exit_code = -1
    if exit_code != 0:
        app.logger.error(stdout)
        raise subprocess.SubprocessError()
    else:
        app.logger.info(stdout)


def _log(level, message, request):
    client_info = {
        "ip_address": request.remote_addr,
        "user_agent": request.user_agent.string,
        "requested_url": request.url,
        "http_method": request.method,
    }
    getattr(app.logger, level)(f"{message} Client info: {client_info}")


@app.route("{{ openwisp2_wireguard_flask_endpoint }}", methods=["POST"])
def update_vpn_config():
    _log("info", "Received request to update VPN config", request)
    request_key = request.args.get("key")
    if not request_key or not hmac.compare_digest(request_key, KEY):
        _log(
            "warning",
            "Authentication failed - invalid or missing key provided.",
            request,
        )
        return Response(status=403)
    for script in UPDATER_SCRIPTS:
        try:
            _exec_command(script)
        except subprocess.SubprocessError:
            _log("error", f'Failed to execute script: "{script}"', request)
            return Response(status=500)
        else:
            _log("info", "Script executed successfully", request)
    return Response(status=200)


@app.errorhandler(500)
def handle_500_error(exception):
    app.logger.error("An internal error occurred: %s", str(exception))
    return Response(status=500)


@app.after_request
def set_security_headers(response):
    security_headers = {
        "Content-Security-Policy": "default-src 'self'",
        "X-Frame-Options": "SAMEORIGIN",
        "X-Content-Type-Options": "nosniff",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    for header, value in security_headers.items():
        response.headers[header] = value
    return response


if __name__ == "__main__":
    app.run()
