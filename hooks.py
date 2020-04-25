import os
import django
import subprocess

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opw.settings")
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db import transaction
from app.models import Clients, CoinSlot, Settings, Rates, Ledger, CoinQueue, Network
import requests
import time
import OPi.GPIO as GPIO
import multiprocessing
import threading
import logging
from datetime import timedelta

logging.basicConfig(filename='cid.log', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

settings = Settings.objects.get(id=1)	
input_pin = settings.Coinslot_Pin
light_pin = settings.Light_Pin
rate_type = settings.Rate_Type
base_rate = settings.Base_Value
timeout = settings.Slot_Timeout

global_bandwidth = Network.objects.get(id=1)
upload_rate = global_bandwidth.Upload_Rate
download_rate = global_bandwidth.Download_Rate

iface = 'eth1'

if upload_rate:
	cmd = ['tcset', iface, '--rate', '{}kbps'.format(upload_rate), '--direction', 'incoming']
	up_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	logging.info(up_res.stdout)
	logging.error(up_res.stderr)

if download_rate:
	cmd = ['tcset', iface, '--rate', '{}kbps'.format(download_rate), '--direction', 'outgoing']
	dn_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	logging.info(dn_res.stdout)
	logging.error(dn_res.stderr)

lights = 0
process = None
event = None

GPIO.setboard(GPIO.PCPCPLUS)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(light_pin, GPIO.OUT)

def insert_coin(pulseCount):	
	slot = CoinSlot.objects.get(id=1)
	client = slot.Client
	n_settings = Settings.objects.get(id=1)	
	n_rate = n_settings.Base_Value

	try:
		rates = Rates.objects.get(Pulse=pulseCount)
	except ObjectDoesNotExist:
		pass

	else:
		if client:
			ledger = Ledger()
			ledger.Client = client
			ledger.Denomination = rates.Denom
			ledger.Slot_No = 1
			ledger.save()

			if rate_type == 'auto':
				new_time = n_rate * rates.Denom
			else:
				new_time = rates.Minutes

			q, _ = CoinQueue.objects.get_or_create(Client=client)
			q.Total_Coins += rates.Denom
			q.Total_Time += new_time
			q.save()

			slot.Last_Updated = timezone.now()
			slot.save()

def main():
	startTime = time.time()
	prev_state = True
	pulseCount = 0
	maxElapsedTime = .3
	sleepTime = .01

	while True:
		light_state = GPIO.input(light_pin)

		if light_state:
			state = GPIO.input(input_pin)
			if state == False and prev_state == True:
				startTime = time.time()
				pulseCount += 1
			else:
				elapsedTime = time.time() - startTime
				if elapsedTime > maxElapsedTime and pulseCount > 0:
					insert_thread = threading.Thread(target=insert_coin, args=(pulseCount, ))
					insert_thread.daemon = True
					insert_thread.start()

					pulseCount = 0
					startTime = time.time()

			time.sleep(sleepTime)
			prev_state = state
		else:
			break

if __name__ == '__main__':
	try:
		with transaction.atomic():
			conn_clients = Clients.objects.filter(Status="Connected")
			for client in conn_clients:
				client.Expire_On = timezone.now() + client.Time_Left
				client.Status = 'Paused'
				client.save()

		logging.info('Started Listening to Coinslot')
		while True:
			slot = CoinSlot.objects.get(id=1)
			time_diff = timedelta.total_seconds(timezone.now()-slot.Last_Updated)
			light_status = GPIO.input(light_pin)

			if timedelta(seconds=time_diff).total_seconds() <= timeout:
				if light_status == False:
					GPIO.output(light_pin, 1)
					main_thread = threading.Thread(target=main)
					main_thread.daemon = True
					main_thread.start()
			else:
				if light_status == True:
					GPIO.output(light_pin, 0)

			time.sleep(1)

	except Exception as e:
		logging.error('Error occured' + str(e))

	finally:
		GPIO.cleanup()