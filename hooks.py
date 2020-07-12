import os
import django
import subprocess

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opw.settings")
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db import transaction
from app.models import Clients, CoinSlot, Settings, Rates, Ledger, CoinQueue, Network, Device
from app.opw import fprint
from pathlib import Path
import requests
import time

#Enable below instead if running on Orange PI One SBC
#import OPi.GPIO as GPIO

import RPi.GPIO as GPIO
import multiprocessing
import threading
import logging
from datetime import timedelta

LOG_PATH = Path(__file__).parent / 'cid.log'
logging.basicConfig(filename=LOG_PATH, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

settings = Settings.objects.get(id=1)	
input_pin = settings.Coinslot_Pin
light_pin = settings.Light_Pin
rate_type = settings.Rate_Type
base_rate = settings.Base_Value
timeout = settings.Slot_Timeout

#Enable below if running on Orange PI One SBC
#GPIO.setboard(GPIO.PCPCPLUS)

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

			q, _ = CoinQueue.objects.get_or_create(Client=client)
			q.Total_Coins += rates.Denom
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
		dev = Device.objects.get(pk=1)
		fp = fprint()
		if fp:
			dev.Ethernet_MAC = fp['eth0_mac']
			dev.Device_SN = fp['serial']
		dev.action = 0
		dev.save()
		
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
		logging.error(str(e))
	finally:
		GPIO.cleanup()
