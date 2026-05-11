import PySimpleGUI as sg

from proxmox.vm_manager import get_available_vms
from proxmox.spice import connect_spice



def show_vm_window():

    vms = get_available_vms()

    layout = []

    for vm in vms:

        layout.append([
            sg.Text(vm['name'], size=(30, 1)),
            sg.Button(
                'Conectar',
                key=f"connect_{vm['vmid']}"
            )
        ])

    layout.append([
        sg.Button('Salir')
    ])

    window = sg.Window('Escritorios Virtuales', layout)

    while True:

        event, values = window.read()

        if event in ('Salir', sg.WINDOW_CLOSED, None):
            break

        if event.startswith('connect_'):

            vmid = event.split('_')[1]

            for vm in vms:
                if str(vm['vmid']) == vmid:
                    connect_spice(vm['node'], vmid)

    window.close()