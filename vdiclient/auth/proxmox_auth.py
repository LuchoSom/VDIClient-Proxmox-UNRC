import random
import proxmoxer
import requests

from config.settings import AppState


def authenticate(username, password=None, otp=None):

    random.shuffle(AppState.hosts[AppState.current_hostset]['hostpool'])

    for hostinfo in AppState.hosts[AppState.current_hostset]['hostpool']:

        host = hostinfo['host']
        port = hostinfo.get('port', 8006)

        try:
            AppState.proxmox = proxmoxer.ProxmoxAPI(
                host,
                user=f"{username}@pve",
                password=password,
                otp=otp,
                verify_ssl=False,
                port=port
            )

            return True

        except proxmoxer.backends.https.AuthenticationError:
            return False

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout
        ):
            continue

    return False