from utils.config_loader import load_config
from utils.system import setup_viewer_command
from gui.login_window import login_window
from gui.vm_window import show_vm_window
from config.settings import AppState


def main():
    setup_viewer_command()
    load_config()

    while True:
        authenticated = login_window()

        if not authenticated:
            break

        show_vm_window()


if __name__ == '__main__':
    main()