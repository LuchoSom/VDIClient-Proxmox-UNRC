from configparser import ConfigParser
from config.settings import AppState
import os
import json

CONFIG_FILE = "vdiclient.ini"


def load_config():
    config = ConfigParser()

    if not os.path.exists(CONFIG_FILE):
        raise Exception(f"No existe {CONFIG_FILE}")

    config.read(CONFIG_FILE)

    if 'General' not in config:
        raise Exception("Falta sección [General]")

    # =========================
    # GENERAL
    # =========================

    AppState.title = config['General'].get(
        'title',
        'VDI Client'
    )

    AppState.theme = config['General'].get(
        'theme',
        'LightBlue'
    )

    # =========================
    # HOSTS
    # =========================

    AppState.hosts = {}

    #
    # CONFIG VIEJA
    #
    if 'Authentication' in config:

        AppState.current_hostset = 'DEFAULT'

        AppState.hosts['DEFAULT'] = {
            'hostpool': [],
            'backend': 'pve',
            'user': '',
            'token_name': None,
            'token_value': None,
            'verify_ssl': False
        }

        if 'Hosts' not in config:
            raise Exception("Falta sección [Hosts]")

        for host in config['Hosts']:

            AppState.hosts['DEFAULT']['hostpool'].append({
                'host': host,
                'port': int(config['Hosts'][host])
            })

        auth = config['Authentication']

        AppState.hosts['DEFAULT']['backend'] = auth.get(
            'auth_backend',
            'pve'
        )

        AppState.hosts['DEFAULT']['user'] = auth.get(
            'user',
            ''
        )

        AppState.hosts['DEFAULT']['token_name'] = auth.get(
            'token_name',
            None
        )

        AppState.hosts['DEFAULT']['token_value'] = auth.get(
            'token_value',
            None
        )

        AppState.hosts['DEFAULT']['verify_ssl'] = auth.getboolean(
            'tls_verify',
            fallback=False
        )

    #
    # CONFIG NUEVA
    #
    else:

        first = True

        for section in config.sections():

            if section.startswith('Hosts.'):

                _, group = section.split('.', 1)

                if first:
                    AppState.current_hostset = group
                    first = False

                AppState.hosts[group] = {
                    'hostpool': [],
                    'backend': 'pve',
                    'user': '',
                    'token_name': None,
                    'token_value': None,
                    'verify_ssl': False
                }

                hostpool = json.loads(
                    config[section]['hostpool']
                )

                for host, port in hostpool.items():

                    AppState.hosts[group]['hostpool'].append({
                        'host': host,
                        'port': int(port)
                    })

                AppState.hosts[group]['backend'] = config[
                    section
                ].get('auth_backend', 'pve')

                AppState.hosts[group]['user'] = config[
                    section
                ].get('user', '')

                AppState.hosts[group]['token_name'] = config[
                    section
                ].get('token_name', None)

                AppState.hosts[group]['token_value'] = config[
                    section
                ].get('token_value', None)

                AppState.hosts[group]['verify_ssl'] = config[
                    section
                ].getboolean(
                    'tls_verify',
                    fallback=False
                )

    print("[INFO] Config cargada correctamente")
    print(AppState.hosts)
    if AppState.hosts:
        AppState.current_hostset = list(AppState.hosts.keys())[0]

    print(f"[INFO] Hostset actual: {AppState.current_hostset}")