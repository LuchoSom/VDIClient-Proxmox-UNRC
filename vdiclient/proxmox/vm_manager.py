from config.settings import AppState


def get_available_vms():

    vms = []

    nodes_online = []

    for node in AppState.proxmox.cluster.resources.get(type='node'):
        if node['status'] == 'online':
            nodes_online.append(node['node'])

    for vm in AppState.proxmox.cluster.resources.get(type='vm'):

        if vm['node'] not in nodes_online:
            continue

        if vm.get('template'):
            continue

        vms.append(vm)

    return vms