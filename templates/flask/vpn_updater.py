import subprocess
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.security import safe_str_cmp


from flask import Flask, Response, request

app = Flask(__name__)

KEY = '{{ openwisp2_wireguard_flask_key }}'
UPDATER_SCRIPTS = [
    '{{ openwisp2_wireguard_path }}/update_wireguard.sh check_config',
]
ALLOWED_SCRIPTS = ["update_wireguard.sh check_config"]


file_handler = RotatingFileHandler('{{ openwisp2_wireguard_path }}/log/openwisp-vpnupdater.log', maxBytes=104857600, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

def is_script_allowed(script):
    return script in ALLOWED_SCRIPTS

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
        app.logger.error("Script execution failed: %s, Error: %s", command, stderr.decode('utf-8'))
        raise subprocess.SubprocessError()


@app.route('{{ openwisp2_wireguard_flask_endpoint }}', methods=['POST'])
def update_vpn_config():
    app.logger.info("Received request to update VPN config")
    #changed this so we can do input validation and prevent timing hacks
    provided_key = request.args.get('key')
    if not provided_key or not safe_str_cmp(provided_key, KEY):
        #make sure we log attempts to get through with an invalid key.
        client_info = {
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string,
            'requested_url': request.url,
            'http_method': request.method
        }
        app.logger.warning("Authentication failed - invalid or missing key provided. Client info: %s", client_info)
        return Response(status=403)
    for script in UPDATER_SCRIPTS:
        try:
            #make sure the called scripted is what we expect it to be and if it isn't then exit unauthorized
            if not is_script_allowed(script):
                app.logger.error("Unauthorized script access attempt: %s", script)
                return Response(status=403)
            _exec_command(script)
            app.logger.info("Script executed successfully: %s", script)
        except subprocess.SubprocessError:
            app.logger.error("Script execution failed: %s", script)
            return Response(status=500)
    return Response(status=200)

@app.errorhandler(500)
def handle_500_error(exception):
    app.logger.error("An internal error occurred: %s", str(exception))
    return Response(status=500)
from flask import Flask, Response

@app.after_request
def set_csp(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
@app.after_request
def set_x_frame_options(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response
@app.after_request
def set_x_content_type_options(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
@app.after_request
def set_hsts(response):
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
@app.after_request
def set_x_xss_protection(response):
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
@app.after_request
def set_referrer_policy(response):
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


if __name__ == '__main__':
    app.run()
