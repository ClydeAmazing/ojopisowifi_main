from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions, status
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDate
from app import models
from app.opw import cc, grc

class DashboardDetails(APIView):
	def post(self, request, format=None):
		action = request.data.get("action", None)

		if not action:
			return Response(status=status.HTTP_404_NOT_FOUND)

		try:
			if action == 'reset':
				models.Ledger.objects.all().delete()
				message = 'Success'

			elif action == 'generate':
				if not cc():
					response = dict()
					rc = grc()
					message = rc.decode('utf-8')
				else:
					message = 'Device is already activated'

			elif action == 'activate':
				key = request.data.get('key', None)
				if key:
					result = cc(key)
					if not result:
						message = 'Error'
					else:
						device = models.Device.objects.get(pk=1)
						device.Device_ID = key
						device.save()

						message = 'Success'
				else:
					message = "Error"

			else:
				dev = models.Device.objects.get(pk=1)

				if action == 'poweroff':
					dev.action = 1
				elif action == 'reboot':
					dev.action = 2
				elif action == 'refresh':
					dev.action = 3
				dev.save()

				message = "Success"

		except Exception as e:
			message = str(e)

		response = {
			'message': message
		}
		
		return Response(response)


	def get(self, request, format=None):
		serial_error = 'You obtained an unauthorized copy of the software. Wifi hotspot customizations is limited. Please contact seller.'
		sales_format = request.data.get("sales_format", None)

		info = dict()
		try:
			ledger = models.Ledger.objects.all()

			if sales_format == 'Monthly':
				info['sales_trend'] = ledger.annotate(Period=TruncMonth('Date')).values('Period').annotate(Sales=Sum('Denomination')).values_list('Period', 'Sales')
			else:
				info['sales_trend'] = ledger.annotate(Period=TruncDate('Date')).values('Period').annotate(Sales=Sum('Denomination')).values_list('Period', 'Sales')
		except ObjectDoesNotExist:
			info['sales_trend'] = None

		connected_count = 0
		disconnected_count = 0
		
		clients = models.Clients.objects.all()
		for client in clients:
			if client.Connection_Status == 'Connected':
				connected_count += 1
			else:
				disconnected_count += 1

		info['connected_count'] = connected_count
		info['disconnected_count'] = disconnected_count

		try:
			device = models.Device.objects.get(pk=1)
			cc_res = cc()
			if cc_res or request.user.is_superuser:
				info['message'] = None
			else:
				info['message'] = serial_error

			if not cc_res:
				info['license_status'] = 'Not Activated'
				info['license'] = None
			else:
				info['license_status'] = 'Activated'
				info['license'] = device.Device_ID

			return Response(info, status=status.HTTP_200_OK)

		except ObjectDoesNotExist:
			info['message'] = serial_error
			return Response(info, status=status.HTTP_200_OK)