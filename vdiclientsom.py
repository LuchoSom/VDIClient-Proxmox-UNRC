#!/usr/bin/env python3
import proxmoxer # pip install proxmoxer
import PySimpleGUI as sg # pip install PySimpleGUI
gui = 'TK'
import requests
from datetime import datetime
from configparser import ConfigParser
import argparse
import random
import sys
import os
import json
import subprocess
from time import sleep
from io import StringIO

# Se crea una ventana invisible solo para obtener las dimensiones de la pantalla
wsize = sg.Window('', [[]], finalize=True)
screen_width = wsize.TKroot.winfo_screenwidth()
screen_height = wsize.TKroot.winfo_screenheight()
#print(screen_width, screen_height)
wsize.close()

class G:
	spiceproxy_conv = {}
	proxmox = None
	icon = None
	vvcmd = None
	scaling = 1
	#########
	inidebug = False
	addl_params = None
	imagefile = None
	kiosk = False
	viewer_kiosk = True
	fullscreen = True
	show_reset = False
	show_hibernate = False
	current_hostset = 'DEFAULT'
	title = 'Iniciar Sesión'
	hosts = {}
	theme = 'LightBlue'
	guest_type = 'both'
	width = None
	height = None


def loadconfig(config_location = None, config_type='file', config_username = None, config_password = None, ssl_verify = True):
	config = ConfigParser(delimiters='=')
	if config_type == 'file':
		if config_location:
			if not os.path.isfile(config_location):
				win_popup_button(f'No se puede leer la configuración proporcionada:\n{config_location} no existe!', 'OK')
				return False
		else:
			if os.name == 'nt': # Windows
				config_list = [
					f'{os.getenv("APPDATA")}\\VDIClient\\vdiclient.ini',
					f'{os.getenv("PROGRAMFILES")}\\VDIClient\\vdiclient.ini',
					f'{os.getenv("PROGRAMFILES(x86)")}\\VDIClient\\vdiclient.ini',
					'C:\\Program Files\\VDIClient\\vdiclient.ini'
				]
				
			elif os.name == 'posix': #Linux
				config_list = [
					os.path.expanduser('~/.config/VDIClient/vdiclient.ini'),
					'/etc/vdiclient/vdiclient.ini',
					'/usr/local/etc/vdiclient/vdiclient.ini'
				]
		for location in config_list:
			if os.path.exists(location):
				config_location = location
				break
		if not config_location:
			win_popup_button(f'No se puede leer la configuración proporcionada desde ninguna ubicación!', 'OK')
			return False
		try:
			config.read(config_location)
		except Exception as e:
			win_popup_button(f'No se puede leer el archivo de configuración:\n{e!r}', 'OK')
			return False
	elif config_type == 'http':
		if not config_location:
			win_popup_button('--config_type http definido, pero no se proporcionó una URL en el parámetro --config_location!', 'OK')
			return False
		try:
			if config_username and config_password:
				r = requests.get(url=config_location, auth=(config_username, config_password), verify = ssl_verify)
			else:
				r = requests.get(url=config_location, verify = ssl_verify)
			config.read_string(r.text)
		except Exception as e:
			win_popup_button(f"No se puede leer la configuración desde la URL!\n{e}", "OK")
			return False
	if not 'General' in config:
		win_popup_button('No se puede leer la configuración proporcionada:\n¡No se ha definido la sección `General`!', 'OK')
		return False
	else:
		if 'title' in config['General']:
			G.title = config['General']['title']
		if 'theme' in config['General']:
			G.theme = config['General']['theme']
		if 'icon' in config['General']:
			if os.path.exists(config['General']['icon']):
				G.icon = config['General']['icon']
		if 'logo' in config['General']:
			if os.path.exists(config['General']['logo']):
				G.imagefile = config['General']['logo']
		if 'kiosk' in config['General']:
			G.kiosk = config['General'].getboolean('kiosk')
		if 'viewer_kiosk' in config['General']:
			G.viewer_kiosk = config['General'].getboolean('viewer_kiosk')
		if 'fullscreen' in config['General']:
			G.fullscreen = config['General'].getboolean('fullscreen')
		if 'inidebug' in config['General']:
			G.inidebug = config['General'].getboolean('inidebug')
		if 'guest_type' in config['General']:
			G.guest_type = config['General']['guest_type']
		if 'show_reset' in config['General']:
			G.show_reset = config['General'].getboolean('show_reset')
		if 'window_width' in config['General']:
			G.width = screen_width
		if 'window_height' in config['General']:
			G.height = screen_height
	if 'Authentication' in config: #Legacy configuration
		G.hosts['DEFAULT'] = {
			'hostpool' : [],
			'backend' : 'pve',
			'user' : "",
			'token_name' : None,
			'token_value' : None,
			'totp' : False,
			'verify_ssl' : True,
			'pwresetcmd' : None,
			'auto_vmid' : None,
			'knock_seq': []
		}
		if not 'Hosts' in config:
			win_popup_button(f'No se puede leer la configuración proporcionada:\n¡No se ha definido la sección `Hosts`!', 'OK')
			return False
		for key in config['Hosts']:
			G.hosts['DEFAULT']['hostpool'].append({
				'host': key,
				'port': int(config['Hosts'][key])
			})
		if 'auth_backend' in config['Authentication']:
			G.hosts['DEFAULT']['backend'] = config['Authentication']['auth_backend']
		if 'user' in config['Authentication']:
			G.hosts['DEFAULT']['user'] = config['Authentication']['user']
		if 'token_name' in config['Authentication']:
			G.hosts['DEFAULT']['token_name'] = config['Authentication']['token_name']
		if 'token_value' in config['Authentication']:
			G.hosts['DEFAULT']['token_value'] = config['Authentication']['token_value']
		if 'auth_totp' in config['Authentication']:
			G.hosts['DEFAULT']['totp'] = config['Authentication'].getboolean('auth_totp')
		if 'tls_verify' in config['Authentication']:
			G.hosts['DEFAULT']['verify_ssl'] = config['Authentication'].getboolean('tls_verify')
		if 'pwresetcmd' in config['Authentication']:
			G.hosts['DEFAULT']['pwresetcmd'] = config['Authentication']['pwresetcmd']
		if 'auto_vmid' in config['Authentication']:
			G.hosts['DEFAULT']['auto_vmid'] = config['Authentication'].getint('auto_vmid')
		if 'knock_seq' in config['Authentication']:
			try:
				G.hosts['DEFAULT']['knock_seq'] = json.loads(config['Authentication']['knock_seq'])
			except Exception as e:
				win_popup_button(f'Knock sequence not valid JSON, skipping!\n{e!r}', 'OK')
	else: # New style config
		i = 0
		for section in config.sections():
			if section.startswith('Hosts.'):
				_, group = section.split('.', 1)
				if i == 0:
					G.current_hostset = group
				G.hosts[group] = {
					'hostpool' : [],
					'backend' : 'pve',
					'user' : "",
					'token_name' : None,
					'token_value' : None,
					'totp' : False,
					'verify_ssl' : True,
					'pwresetcmd' : None,
					'auto_vmid' : None,
					'knock_seq': []
				}
				try:
					hostjson = json.loads(config[section]['hostpool'])
				except Exception as e:
					win_popup_button(f"Error: no se pudo analizar el grupo de hosts en la sección {section}:\n{e!r}", "OK")
					return False
				for key, value in hostjson.items():
					G.hosts[group]['hostpool'].append({
						'host': key,
						'port': int(value)
					})
				if 'auth_backend' in config[section]:
					G.hosts[group]['backend'] = config[section]['auth_backend']
				if 'user' in config[section]:
					G.hosts[group]['user'] = config[section]['user']
				if 'token_name' in config[section]:
					G.hosts[group]['token_name'] = config[section]['token_name']
				if 'token_value' in config[section]:
					G.hosts[group]['token_value'] = config[section]['token_value']
				if 'auth_totp' in config[section]:
					G.hosts[group]['totp'] = config[section].getboolean('auth_totp')
				if 'tls_verify' in config[section]:
					G.hosts[group]['verify_ssl'] = config[section].getboolean('tls_verify')
				if 'pwresetcmd' in config[section]:
					G.hosts[group]['pwresetcmd'] = config[section]['pwresetcmd']
				if 'auto_vmid' in config[section]:
					G.hosts[group]['auto_vmid'] = config[section].getint('auto_vmid')
				if 'knock_seq' in config[section]:
					try:
						G.hosts[group]['knock_seq'] = json.loads(config[section]['knock_seq'])
					except Exception as e:
						win_popup_button(f'Knock sequence not valid JSON, skipping!\n{e!r}', 'OK')
				i += 1
	if 'SpiceProxyRedirect' in config:
		for key in config['SpiceProxyRedirect']:
			G.spiceproxy_conv[key] = config['SpiceProxyRedirect'][key]
	if 'AdditionalParameters' in config:
		G.addl_params = {}
		for key in config['AdditionalParameters']:
			G.addl_params[key] = config['AdditionalParameters'][key]
	return True

def win_popup(message):
	layout = [
		[sg.Text(message, key='-TXT-')]
	]
	window = sg.Window('Message', layout,  location=(screen_width//2, screen_height//2), return_keyboard_events=True, no_titlebar=True, keep_on_top=True, finalize=True)
	window.bring_to_front()
	_, _ = window.read(timeout=10) # Fixes a black screen bug
	window['-TXT-'].update(message)
	sleep(.15)
	window['-TXT-'].update(message)
	return window
	
def win_popup_button(message, button):
	layout = [
				[sg.Text(message)],
				[sg.Button(button)]
			]
	window = sg.Window('Message', layout, location=(screen_width//2, screen_height//2), return_keyboard_events=True, no_titlebar=True, keep_on_top=True, finalize=True)
	window.Element(button).SetFocus()
	
	while True:
		event, values = window.read()
		if event in (button, sg.WIN_CLOSED, 'Aceptar', '\r', 'special 16777220', 'special 16777221'):
			window.close()
			return
		

def setmainlayout():
    readonly = False
    if G.hosts[G.current_hostset]['user'] and G.hosts[G.current_hostset]['token_name'] and G.hosts[G.current_hostset]['token_value']:
        readonly = True

    layout = []
    
    # Ajuste en el título con pad y justification únicamente
    if G.imagefile:
        layout.append(
            [
                sg.Text(
                    G.title,
                    #size=(18 * G.scaling, 1 * G.scaling),
                    justification='center',
                    font=["Times New Roman", 24, "bold"],
                    pad=((630, 0), (0, 0))  # Ajuste de padding arriba para centrar el título
                ),
                sg.Image(G.imagefile, pad=((20, 0), (5, 0)))  # Ajuste padding para la imagen
            ]
        )
    else:
        layout.append(
            [
                sg.Text(
                    G.title,
                    #size=(40 * G.scaling, 1 * G.scaling),
                    justification='center',
                    font=["Times New Roman", 24, "bold"],
                    pad=((630, 0), (0, 0))  # Espacio arriba y abajo del título
                )
            ]
        )
    
    if len(G.hosts) > 1:
        groups = []
        for key, _ in G.hosts.items():
            groups.append(key)
        layout.append(
            [
                sg.Text(
                    "Grupo de Servidores:",
                    size=(12 * G.scaling, 1 * G.scaling),
                    font=["Helvetica", 12],
                    pad=((200, 0), (10, 10))
                ),
                sg.Combo(
                    groups,
                    G.current_hostset,
                    key='-group-',
                    font=["Helvetica", 12],
                    pad=((10, 0), (10, 10)),
                    readonly=True,
                    enable_events=True
                )
            ]
        )

    layout.append(
        [
            sg.Text(
                "Usuario:",
                #size=(12 * G.scaling, 1 * G.scaling),
                font=["Helvetica", 12],
                pad=((630, 48), (100, 0))
            ),
            sg.InputText(
                default_text=G.hosts[G.current_hostset]['user'],
                key='-username-',
                font=["Helvetica", 12],
                pad=((0, 0), (98, 0)),
				background_color='#66B4B9',
                readonly=readonly
            )
        ]
    )
    layout.append(
        [
            sg.Text(
                "Contraseña:",
                size=(12 * G.scaling, 1 * G.scaling),
                font=["Helvetica", 12],
                pad=((630, 0), (10, 0))
            ),
            sg.InputText(
                key='-password-',
                password_char='*',
                font=["Helvetica", 12],
                pad=((0, 0), (8, 0)),
				background_color='#66B4B9',
                readonly=readonly
            )
        ]
    )
    
    if G.hosts[G.current_hostset]['totp']:
        layout.append(
            [
                sg.Text(
                    "OTP Key",
                    size=(12 * G.scaling, 1),
                    font=["Helvetica", 12]
                ),
                sg.InputText(
                    key='-totp-',
                    font=["Helvetica", 12]
                )
            ]
        )
    if G.kiosk:
        layout.append(
            [
                sg.Button(
                    "Aceptar",
                    font=["Helvetica", 14],
                    bind_return_key=True,
					pad=((630, 0), (0, 0))
                )
            ]
        )
    else:
        layout.append(
            [
                sg.Button(
                    "Aceptar",
                    font=["Helvetica", 14],
                    bind_return_key=True,
					pad=((960, 0), (20, 0)),
					button_color=("white", "#66B4B9")
                ),
                sg.Button(
                    "Cancelar",
                    font=["Helvetica", 14],
					pad=((0, 0), (20, 0)),
					button_color=("white", "#66B4B9")
                )
            ]
        )
    if G.hosts[G.current_hostset]['pwresetcmd']:
        layout[-1].append(
            sg.Button(
                'Password Reset',
                font=["Helvetica", 14]
            )
        )
    return layout


def getvms(listonly = False):
	vms = []
	try:
		nodes = []
		for node in G.proxmox.cluster.resources.get(type='node'):
			if node['status'] == 'online':
				nodes.append(node['node'])

		for vm in G.proxmox.cluster.resources.get(type='vm'):
			if vm['node'] not in nodes:
				continue
			if 'template' in vm and vm['template']:
				continue
			if G.guest_type == 'both' or G.guest_type == vm['type']:
				if listonly:
					vms.append(
						{
							'vmid': vm['vmid'],
							'name': vm['name'],
							'node': vm['node']
						}
					)
				else:
					vms.append(vm)
		return vms
	except proxmoxer.core.ResourceException as e:
		win_popup_button(f"No se puede mostrar la lista de MVs:\n {e!r}", 'OK')
		return False
	except requests.exceptions.ConnectionError as e:
		print(f"Encountered error when querying proxmox: {e!r}")
		return False

def setvmlayout(vms):
	layout = []
	if G.imagefile:
		layout.append([sg.Text(
                    	G.title,
                    	#size=(18 * G.scaling, 1 * G.scaling),
                    	justification='center',
                    	font=["Times New Roman", 24, "bold"],
                    	pad=((630, 0), (0, 0))  # Ajuste de padding 
                ),
                sg.Image(G.imagefile, pad=((20, 0), (5, 0)))])
	else:
		layout.append([sg.Text(G.title, size =(30*G.scaling, 1*G.scaling), justification='c', font=["Helvetica", 18])])
	layout.append([sg.Text('Selecciona un escritorio:', size =(40*G.scaling, 1*G.scaling), justification='c', font=["Times New Roman", 18], pad=((0, 100), (100, 30)))])
	layoutcolumn = []
	for vm in vms:
		if not vm["status"] == "unknown":
			vmkeyname = f'-VM|{vm["vmid"]}-'
			connkeyname = f'-CONN|{vm["vmid"]}-'
			resetkeyname = f'-RESET|{vm["vmid"]}-'
			hiberkeyname = f'-HIBER|{vm["vmid"]}-'
			state = 'Apagada'
			connbutton = sg.Button('Conectar', font=["Helvetica", 14], key=connkeyname, button_color=("white", "#66B4B9"), pad=((0, 0), (0, 0)))
			if vm['status'] == 'running':
				if 'lock' in vm:
					state = vm['lock']
					if state in ('suspending', 'suspended'):
						if state == 'suspended':
							state = 'starting'
						connbutton = sg.Button('Conectar', font=["Helvetica", 14], button_color=("white", "#66B4B9"), pad=((0, 0), (80, 0)), key=connkeyname, disabled=True)
				else:
					state = vm['status']
			tmplayout =	[
				sg.Text(vm['name'], font=["Times New Roman", 16], size=(22*G.scaling, 1*G.scaling), pad=((0, 0), (0, 0))),
				sg.Text(f"Estado: Encendida", font=["Times New Roman", 16], size=(22*G.scaling, 1*G.scaling), pad=((0, 0), (0, 0)), key=vmkeyname),
				connbutton
			]
			if G.show_reset:
				tmplayout.append(
					sg.Button('Reset', font=["Helvetica", 14], key=resetkeyname)
				)
			if G.show_hibernate:
				tmplayout.append(
					sg.Button('Hibernate', font=["Helvetica", 14], key=hiberkeyname)
				)
			layoutcolumn.append(tmplayout)
			layoutcolumn.append([sg.HorizontalSeparator()])
	if len(vms) > 5: # We need a scrollbar
		layout.append([sg.Column(layoutcolumn, scrollable = True, size = [None, None] )])
	else:
		for row in layoutcolumn:
			layout.append(row)
	layout.append([sg.Button('Salir', font=["Helvetica", 14], button_color=("white", "#66B4B9"), pad=((488, 0), (0, 0)))])
	return layout

def iniwin(inistring):
	inilayout = [
			[sg.Multiline(default_text=inistring, size=(100, 40))]
	]
	iniwindow = sg.Window('INI debug', inilayout)
	while True:
		event, values = iniwindow.read()
		if event == None:
			break
	iniwindow.close()
	return True

def vmaction(vmnode, vmid, vmtype, action='Conectar'):
	status = False
	if vmtype == 'qemu':
		vmstatus = G.proxmox.nodes(vmnode).qemu(str(vmid)).status.get('current')
	else: # Not sure this is even a thing, but here it is...
		vmstatus = G.proxmox.nodes(vmnode).lxc(str(vmid)).status.get('current')
	if action == 'reload':
		stoppop = win_popup(f'Stopping {vmstatus["name"]}...')
		sleep(.1)
		try:
			if vmtype == 'qemu':
				jobid = G.proxmox.nodes(vmnode).qemu(str(vmid)).status.stop.post(timeout=28)
			else: # Not sure this is even a thing, but here it is...
				jobid = G.proxmox.nodes(vmnode).lxc(str(vmid)).status.stop.post(timeout=28)
		except proxmoxer.core.ResourceException as e:
			stoppop.close()
			win_popup_button(f"No se puede detener la MV, por favor proporciona a tu administrador del sistema el siguiente error:\n {e!r}", 'OK')
			return False
		running = True
		i = 0
		while running and i < 30:
			try:
				jobstatus = G.proxmox.nodes(vmnode).tasks(jobid).status.get()
			except Exception:
				# We ran into a query issue here, going to skip this round and try again
				jobstatus = {}
			if 'exitstatus' in jobstatus:
				stoppop.close()
				stoppop = None
				if jobstatus['exitstatus'] != 'OK':
					win_popup_button('No se puede detener la MV, por favor contacta a tu administrador del sistema para obtener asistencia', 'OK')
					return False
				else:
					running = False
					status = True
			sleep(1)
			i += 1
		if not status:
			if stoppop:
				stoppop.close()
			return status
	status = False
	if vmtype == 'qemu':
		vmstatus = G.proxmox.nodes(vmnode).qemu(str(vmid)).status.get('current')
	else: # Not sure this is even a thing, but here it is...
		vmstatus = G.proxmox.nodes(vmnode).lxc(str(vmid)).status.get('current')
	sleep(.2)
	if vmstatus['status'] != 'running':
		startpop = win_popup(f'Starting {vmstatus["name"]}...')
		sleep(.1)
		try:
			if vmtype == 'qemu':
				jobid = G.proxmox.nodes(vmnode).qemu(str(vmid)).status.start.post(timeout=28)
			else: # Not sure this is even a thing, but here it is...
				jobid = G.proxmox.nodes(vmnode).lxc(str(vmid)).status.start.post(timeout=28)
		except proxmoxer.core.ResourceException as e:
			startpop.close()
			win_popup_button(f"No se puede iniciar la MV, por favor proporciona a tu administrador del sistema el siguiente error:\n {e!r}", 'OK')
			return False
		running = False
		i = 0
		while running == False and i < 30:
			try:
				jobstatus = G.proxmox.nodes(vmnode).tasks(jobid).status.get()
			except Exception:
				# We ran into a query issue here, going to skip this round and try again
				jobstatus = {}
			if 'exitstatus' in jobstatus:
				startpop.close()
				startpop = None
				if jobstatus['exitstatus'] != 'OK':
					win_popup_button('No se puede iniciar la MV, por favor contacta a tu administrador del sistema para obtener asistencia', 'OK')
					running = True
				else:
					running = True
					status = True
			sleep(1)
			i += 1
		if not status:
			if startpop:
				startpop.close()
			return status
	if action == 'reload':
		return
	try:
		if vmtype == 'qemu':
			spiceconfig = G.proxmox.nodes(vmnode).qemu(str(vmid)).spiceproxy.post()
		else: # Not sure this is even a thing, but here it is...
			spiceconfig = G.proxmox.nodes(vmnode).lxc(str(vmid)).spiceproxy.post()
	except proxmoxer.core.ResourceException as e:
		win_popup_button(f"No se puede conectar a la MV {vmid}:\n{e!r}\n¿Está configurada la pantalla SPICE para tu MV?", 'OK')
		return False
	confignode = ConfigParser()
	confignode['virt-viewer'] = {}
	for key, value in spiceconfig.items():
		if key == 'proxy':
			val = value[7:].lower()
			if val in G.spiceproxy_conv:
				confignode['virt-viewer'][key] = f'http://{G.spiceproxy_conv[val]}'
			else:
				confignode['virt-viewer'][key] = f'{value}'
		else:
			confignode['virt-viewer'][key] = f'{value}'
	if G.addl_params:
		for key, value in G.addl_params.items():
			confignode['virt-viewer'][key] = f'{value}'
	inifile = StringIO('')
	confignode.write(inifile)
	inifile.seek(0)
	inistring = inifile.read()
	if G.inidebug:
		closed = iniwin(inistring)
	connpop = win_popup(f'Conectando a {vmstatus["name"]}...')
	pcmd = [G.vvcmd]
	if G.kiosk and G.viewer_kiosk:
		pcmd.append('--kiosk')
		pcmd.append('--kiosk-quit')
		pcmd.append('on-disconnect')
	elif G.fullscreen:
		pcmd.append('--full-screen')
	pcmd.append('-') #We need it to listen on stdin
	process = subprocess.Popen(pcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	try:
		output = process.communicate(input=inistring.encode('utf-8'), timeout=5)[0]
	except subprocess.TimeoutExpired:
		pass
	status = True
	connpop.close()
	return status


def setcmd():
	try:
		if os.name == 'nt': # Windows
			import csv
			cmd1 = 'ftype VirtViewer.vvfile'
			result = subprocess.check_output(cmd1, shell=True)
			cmdresult = result.decode('utf-8')
			cmdparts = cmdresult.split('=')
			for row in csv.reader([cmdparts[1]], delimiter = ' ', quotechar = '"'):
				G.vvcmd = row[0]
				break

		elif os.name == 'posix':
			cmd1 = 'which remote-viewer'
			result = subprocess.check_output(cmd1, shell=True)
			G.vvcmd = 'remote-viewer'
	except subprocess.CalledProcessError:
		if os.name == 'nt':
			win_popup_button('Installation of virt-viewer missing, please install from https://virt-manager.org/download/', 'OK')
		elif os.name == 'posix':
			win_popup_button('Falta la instalación de virt-viewer, por favor instálalo usando `apt install virt-viewer`', 'OK')
		sys.exit()

def pveauth(username, passwd=None, totp=None):
	random.shuffle(G.hosts[G.current_hostset]['hostpool'])
	err = None
	for hostinfo in G.hosts[G.current_hostset]['hostpool']:
		host = hostinfo['host']
		if 'port' in hostinfo:
			port = hostinfo['port']
		else:
			port = 8006
		connected = False
		authenticated = False
		if not connected and not authenticated:
			try:
				if G.hosts[G.current_hostset]['token_name'] and G.hosts[G.current_hostset]['token_value']:
					G.proxmox = proxmoxer.ProxmoxAPI(
						host,
						user=f"{username}@{G.hosts[G.current_hostset]['backend']}",
						token_name=G.hosts[G.current_hostset]['token_name'],
						token_value=G.hosts[G.current_hostset]['token_value'],
						verify_ssl=G.hosts[G.current_hostset]['verify_ssl'], 
						port=port
					)
				elif totp:
					G.proxmox = proxmoxer.ProxmoxAPI(
						host,
						user=f"{username}@{G.hosts[G.current_hostset]['backend']}",
						otp=totp,
						password=passwd,
						verify_ssl=G.hosts[G.current_hostset]['verify_ssl'],
						port=port
					)
				else:
					G.proxmox = proxmoxer.ProxmoxAPI(
						host,
						user=f"{username}@{G.hosts[G.current_hostset]['backend']}",
						password=passwd,
						verify_ssl=G.hosts[G.current_hostset]['verify_ssl'],
						port=port
					)
				connected = True
				authenticated = True
				return connected, authenticated, err
			except proxmoxer.backends.https.AuthenticationError as e:
				err = e
				connected = True
				return connected, authenticated, err
			except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
				err = e
				connected = False
	return connected, authenticated, err

def loginwindow():
	layout = setmainlayout()
	if G.hosts[G.current_hostset]['user'] and G.hosts[G.current_hostset]['token_name'] and G.hosts[G.current_hostset]['token_value'] and len(G.hosts) == 1: # We need to skip the login
		popwin = win_popup("Por favor espera, autenticando...")
		connected, authenticated, error = pveauth(G.hosts[G.current_hostset]['user'])
		popwin.close()
		if not connected:
			win_popup_button(f'No se puede conectar a ningún servidor VDI, ¿estás conectado a Internet?\nInformación del error: {error}', 'OK')
			return False, False
		elif connected and not authenticated:
			win_popup_button('Nombre de usuario y/o contraseña inválidos, por favor intenta de nuevo!', 'OK', keep_on_top=True)
			return False, False
		elif connected and authenticated:
			return True, False
	else:
		if G.icon:
			window = sg.Window("Universidad Nacional de Río Cuarto", layout, return_keyboard_events=True, resizable=False, no_titlebar=G.kiosk, icon=G.icon, size=(screen_width, screen_height))
		else:
			window = sg.Window("Universidad Nacional de Río Cuarto", layout, return_keyboard_events=True, resizable=False, no_titlebar=G.kiosk, size=(screen_width, screen_height))
		while True:
			event, values = window.read()
			if event == '-group-' and values['-group-'] != G.current_hostset:
				#Switch cluster
				G.current_hostset = values['-group-']
				window.close()
				return False, True
			if event == 'Cancelar' or event == sg.WIN_CLOSED:
				window.close()
				return False, False
			elif event == 'Password Reset':
				try:
					subprocess.check_call(G.hosts[G.current_hostset]['pwresetcmd'], shell=True)
				except Exception as e:
					win_popup_button(f'No se puede abrir el comando de restablecimiento de contraseña.\n\nInformación del error:\n{e}', 'OK')
			else:
				if event in ('Aceptar', '\r', 'special 16777220', 'special 16777221'):
					popwin = win_popup("Por favor espera, autenticando...")
					user = values['-username-']
					passwd = values['-password-']
					totp = None
					if '-totp-' in values:
						if values['-totp-'] not in (None, ''):
							totp = values['-totp-']
					connected, authenticated, error = pveauth(user, passwd=passwd, totp=totp)
					popwin.close()
					if not connected:
						win_popup_button(f'No se puede conectar a ningún servidor VDI, ¿estás conectado a Internet?\nInformación del error: {error}', 'OK')
					elif connected and not authenticated:
						win_popup_button('Nombre de usuario y/o contraseña inválidos, por favor intenta de nuevo.', 'OK')
					elif connected and authenticated:
						window.close()
						return True, False
					#break


def showvms():
	vms = getvms()
	vmlist = getvms(listonly=True)
	newvmlist = vmlist.copy()
	if vms == False:
		return False
	if len(vms) < 1:
		win_popup_button('No se encontraron instancias de escritorio, por favor consulta con tu administrador del sistema', 'OK')
		return False
	layout = setvmlayout(vms)
	if G.icon:
		window = sg.Window(G.title, layout, return_keyboard_events=True, finalize=True, resizable=False, no_titlebar=G.kiosk, size=(screen_width, screen_height), icon=G.icon)
	else:
		window = sg.Window(G.title, layout, return_keyboard_events=True, finalize=True, resizable=False, size=(screen_width, screen_height), no_titlebar=G.kiosk)
	timer = datetime.now()
	while True:
		if (datetime.now() - timer).total_seconds() > 5:
			timer = datetime.now()
			newvmlist = getvms(listonly = True)
			if newvmlist:
				if vmlist != newvmlist:
					vmlist = newvmlist.copy()
					vms = getvms()
					if vms:
						layout = setvmlayout(vms)
						window.close()
						if G.icon:
							window = sg.Window(G.title, layout, return_keyboard_events=True, finalize=True, resizable=False, no_titlebar=G.kiosk, size=(G.width, G.height), icon=G.icon)
						else:
							window = sg.Window(G.title, layout, return_keyboard_events=True,finalize=True, resizable=False, no_titlebar=G.kiosk, size=(G.width, G.height))
					window.bring_to_front()
				else: # Refresh existing vm status
					newvms = getvms()
					if newvms:
						for vm in newvms:
							vmkeyname = f'-VM|{vm["vmid"]}-'
							connkeyname = f'-CONN|{vm["vmid"]}-'
							state = 'Apagada'
							if vm['status'] == 'running':
								if 'lock' in vm:
									state = vm['lock']
									if state in ('suspending', 'suspended'):
										window[connkeyname].update(disabled=True)
										if state == 'suspended':
											state = 'starting'
								else:
									state = vm['status']
									window[connkeyname].update(disabled=False)
							else:
								window[connkeyname].update(disabled=False)
							window[vmkeyname].update(f"Estado: {state}")

		event, values = window.read(timeout = 1000)
		if event in ('Salir', None):
			window.close()
			return False
		if event.startswith('-CONN'):
			eventparams = event.split('|')
			vmid = eventparams[1][:-1]
			found = False
			for vm in vms:
				if str(vm['vmid']) == vmid:
					found = True
					vmaction(vm['node'], vmid, vm['type'])
			if not found:
				win_popup_button(f'La MV {vm["name"]} ya no está disponible, por favor contacta a tu administrador del sistema', 'OK')
		elif event.startswith('-RESET'):
			eventparams = event.split('|')
			vmid = eventparams[1][:-1]
			found = False
			for vm in vms:
				if str(vm['vmid']) == vmid:
					found = True
					vmaction(vm['node'], vmid, vm['type'], action='reload')
			if not found:
				win_popup_button(f'La MV {vm["name"]} ya no está disponible, por favor contacta a tu administrador del sistema', 'OK')
	return True

def main():
	G.scaling = 1 # TKinter requires integers
	parser = argparse.ArgumentParser(description='Proxmox VDI Client')
	parser.add_argument('--list_themes', help='List all available themes', action='store_true')
	parser.add_argument('--config_type', help='Select config type (default: file)', choices=['file', 'http'], default='file')
	parser.add_argument('--config_location', help='Specify the config location (default: search for config file)', default=None)
	parser.add_argument('--config_username', help="HTTP basic authentication username (default: None)", default=None)
	parser.add_argument('--config_password', help="HTTP basic authentication password (default: None)", default=None)
	parser.add_argument('--ignore_ssl', help="HTTPS ignore SSL certificate errors (default: False)", action='store_false', default=True)
	args = parser.parse_args()
	if args.list_themes:
		sg.preview_all_look_and_feel_themes()
		return
	setcmd()
	if not loadconfig(config_location=args.config_location, config_type=args.config_type, config_username=args.config_username, config_password=args.config_password, ssl_verify=args.ignore_ssl):
		return False
	sg.theme(G.theme)
	loggedin = False
	switching = False
	while True:
		if not loggedin:
			loggedin, switching = loginwindow()
			if not loggedin and not switching:
				if G.hosts[G.current_hostset]['user'] and G.hosts[G.current_hostset]['token_name'] and G.hosts[G.current_hostset]['token_value']: # This means if we don't exit we'll be in an infinite loop
					return 1
				break
			elif not loggedin and switching:
				pass
			else:
				if G.hosts[G.current_hostset]['auto_vmid']:
					vms = getvms()
					for row in vms:
						if row['vmid'] == G.hosts[G.current_hostset]['auto_vmid']:
							vmaction(row['node'], row['vmid'], row['type'], action='Conectar')
							return 0
					win_popup_button(f"No se encontró ninguna instancia de VDI con ID {G.hosts[G.current_hostset]['auto_vmid']}!", 'OK')
				vmstat = showvms()
				if not vmstat:
					G.proxmox = None
					loggedin = False
					if G.hosts[G.current_hostset]['user'] and G.hosts[G.current_hostset]['token_name'] and G.hosts[G.current_hostset]['token_value'] and len(G.hosts) == 1: # This means if we don't exit we'll be in an infinite loop
						return 0
				else:
					return

if __name__ == '__main__':
	sys.exit(main())
