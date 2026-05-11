import subprocess
from configparser import ConfigParser
from config.settings import AppState


def connect_spice(node, vmid):

    print(f"[INFO] Conectando VM {vmid} en nodo {node}")

    try:
        spiceconfig = (
            AppState.proxmox
            .nodes(node)
            .qemu(str(vmid))
            .spiceproxy
            .post()
        )

        print("[INFO] Config SPICE ORIGINAL:")
        print(spiceconfig)

    except Exception as e:
        print(f"[ERROR] No se pudo obtener SPICE: {e}")
        return False

    # =========================
    # FIX HOST/IP
    # =========================

    REAL_NODE_IP = {
        "masternode": "192.168.0.12",
        "node1": "192.168.0.13",
        "node3": "192.168.0.15"
    }

    if node in REAL_NODE_IP:
        spiceconfig['proxy'] = f"http://{REAL_NODE_IP[node]}:3128"

    print("[INFO] Config SPICE MODIFICADA:")
    print(spiceconfig)

    # =========================
    # CREAR ARCHIVO VV
    # =========================

    config = ConfigParser()
    config['virt-viewer'] = {}

    for key, value in spiceconfig.items():
        config['virt-viewer'][key] = str(value)

    config['virt-viewer']['fullscreen'] = '1'

    vvfile = f"/tmp/{vmid}.vv"

    with open(vvfile, "w") as f:
        config.write(f)

    print(f"[INFO] Archivo VV: {vvfile}")

    with open(vvfile, "r") as f:
        print(f.read())

    # =========================
    # EJECUTAR REMOTE VIEWER
    # =========================

    try:

        cmd = ['remote-viewer', vvfile]

        print("[INFO] Ejecutando:")
        print(cmd)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate()

        print("\n===== STDOUT =====")
        print(stdout.decode())

        print("\n===== STDERR =====")
        print(stderr.decode())

        print(f"\n[INFO] Return code: {process.returncode}")

        return process.returncode == 0

    except Exception as e:
        print(f"[ERROR] remote-viewer: {e}")
        return False