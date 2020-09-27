from pathlib import Path
import requests
import json, time

#Enable below instead if running on Orange PI One SBC
import OPi.GPIO as GPIO

#import RPi.GPIO as GPIO
import threading
import logging
from datetime import timedelta

LOG_PATH = Path(__file__).parent / 'cid.log'
logging.basicConfig(filename=LOG_PATH, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

#Enable below if running on Orange PI One SBC
GPIO.setboard(GPIO.PCPCPLUS)
GPIO.setmode(GPIO.BOARD)

url = 'http://10.0.0.1/app/pay'
headers = {'X-Requested-With': 'XMLHttpRequest'}
session = requests.Session()

def insert_coin(pulseCount):
	data = {
		'slot_id': 1,
		'identifier': 'n8cy3oKCKM',
		'pulse': pulseCount
	}
	session.post(url, headers=headers, data=data)	

if __name__ == '__main__':
	try:
		while True:
			response = session.get(url, headers=headers)
			status_code = response.status_code
			status_desc = response.reason

			if status_code == 200:
				logging.info('Started Listening to Coinslot')
				json_data = json.loads(response.text)
				input_pin = json_data['settings']['Coinslot_Pin']
				light_pin = json_data['settings']['Light_Pin']
				Slot_Timeout = json_data['settings']['Slot_Timeout']

				GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
				GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.LOW)

				while True:
					light_status = GPIO.input(light_pin)

					if light_status == True:
						startTime = time.time()
						prev_state = True
						pulseCount = 0
						maxElapsedTime = .5
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
									if elapsedTime > Slot_Timeout:
										GPIO.output(light_pin, GPIO.LOW)

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

					time.sleep(1)
			else:
				time.sleep(15)

	except Exception as e:
		logging.error(str(e))
	finally:
		GPIO.cleanup()
