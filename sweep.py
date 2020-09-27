from pathlib import Path
import threading
import subprocess
import requests
import logging
import json
import time

LOG_PATH = Path(__file__).parent / 'opw.log'
logging.basicConfig(filename=LOG_PATH, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

url = 'http://10.0.0.1/app/sweep'
headers = {'X-Requested-With': 'XMLHttpRequest'}

session = requests.Session()
logging.info('NDSCTL Listener Initiated')
action_ready = False

def do_action(code):
	if code == 1:
		res = subprocess.run(['sudo', 'poweroff'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if res.stderr:
			logging.error(res.stderr.decode('utf-8'))
			
	if code == 2:
		res = subprocess.run(['sudo', 'reboot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if res.stderr:
			logging.error(res.stderr.decode('utf-8'))

def notify(payload):
	header = {"Content-Type": "application/json; charset=utf-8"}
	host = "https://onesignal.com/api/v1/notifications"
	requests.post(host, headers=header, data=json.dumps(payload))	


while True:
	response = session.get(url, headers=headers)
	status_code = response.status_code
	status_desc = response.reason

	if status_code == 200:
		json_data = json.loads(response.text)
		clients_list = json_data['clients']
		client_macs = list(x['MAC_Address'] for x in clients_list)
		whitelisted = json_data['whitelist']

		all_client_macs = client_macs + list(set(whitelisted) - set(client_macs))

		action_code = json_data['system_action']
		push_notif = json_data['push_notif']
		push_notif_clients = json_data['push_notif_clients']

		if not action_ready:
			if action_code == 0:
				action_ready = True
		else:
			if action_code != 0:
				do_action(action_code)

		res = subprocess.run(['sudo', 'ndsctl', 'json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		if not res.stderr:
			try:
				s = res.stdout.decode('utf-8')
				s = s.replace('\n', '')
				s = s.replace('}{', ',')
				
				ndsctl_res = json.loads(s)

				if int(ndsctl_res['client_list_length']) > 0:
					ndsctl_conn_macs = list(ndsctl_res['clients'][x]['mac'] for x in ndsctl_res['clients'] if ndsctl_res['clients'][x]['state'] == 'Authenticated')
				else:
					ndsctl_conn_macs = list()

				#Authentication	
				for mac in all_client_macs:
					if mac not in ndsctl_conn_macs:
						res = subprocess.run(['sudo', 'ndsctl', 'auth', mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
						if res.stderr:
							logging.error(res.stderr.decode('utf-8'))

				#Deacuthentication
				for mac in ndsctl_conn_macs:
					if mac not in all_client_macs:
						res = subprocess.run(['sudo', 'ndsctl', 'deauth', mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
						if res.stderr:
							logging.error(res.stderr.decode('utf-8'))

				# Push Notifications
				if push_notif['Enabled'] and push_notif_clients:
					app_id = push_notif['app_id']
					notif_title = push_notif['notification_title']
					notif_message = push_notif['notification_message']

					payload = {
							"app_id": app_id,
							"include_player_ids": push_notif_clients,
							"contents": {"en": notif_message},
							"headings": {"en": notif_title}
							}

					notification_thread = threading.Thread(target=notify, args=(payload, ))
					notification_thread.daemon = True
					notification_thread.start()

			except Exception as e:
				logging.error(e)
		else:
			logging.error(res.stderr.decode('utf-8'))
	else:
		logging.error(' '.join([str(status_code), status_desc]))

	time.sleep(15)
