from config.settings import AppState


def get_cluster_nodes():
    return AppState.proxmox.cluster.resources.get(type='node')


def get_cluster_vms():
    return AppState.proxmox.cluster.resources.get(type='vm')