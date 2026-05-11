import PySimpleGUI as sg

from auth.proxmox_auth import authenticate



def login_window():

    layout = [
        [sg.Text('Usuario')],
        [sg.Input(key='username')],

        [sg.Text('Contraseña')],
        [sg.Input(password_char='*', key='password')],

        [sg.Button('Ingresar')]
    ]

    window = sg.Window('Login', layout)

    while True:

        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, None):
            return False

        if event == 'Ingresar':

            success = authenticate(
                values['username'],
                values['password']
            )

            if success:
                window.close()
                return True

            sg.popup_error('Credenciales inválidas')