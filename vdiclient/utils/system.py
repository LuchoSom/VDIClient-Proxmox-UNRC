import subprocess
import os

from config.settings import AppState



def setup_viewer_command():

    if os.name == 'posix':

        subprocess.check_output(
            'which remote-viewer',
            shell=True
        )

        AppState.viewer_command = 'remote-viewer'