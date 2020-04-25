from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.edit import UpdateView
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F
from django.contrib import messages
from datetime import timedelta
from getmac import getmac
from app.opw import device, fprint
from app import models
# import configparser #
import subprocess #
# import paramiko #
# import socket
# import json
import time
# import uuid
import os
# import hashlib

local_ip = ['::1', '127.0.0.1', '10.0.0.1']

def api_response(code):
    response = dict()

    if code == 200:
        response['code'] = code
        response['status'] = 'Success'
        response['description'] = ''

    if code == 300:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Pay error.'

    if code == 400:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Pay error. Slot Not Found.'

    if code == 500:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Session Timeout. <strong><a href="/app/portal">Click to refresh your browser.</a></strong>'

    if code == 600:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Someone is still paying. Try again.'

    if code == 700:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Invalid action. No changes made.'

    if code == 800:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Client not found.'

    if code == 900:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Unknown coin inserted.'

    if code == 110:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Invalid / Used / Expired voucher code.'

    return  response


class Portal(View):
    template_name = 'captive.html'
    
    def getDeviceInfo(self, request):
        info = dict()
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        mac = getmac.get_mac_address(ip=ip)
        
        info['ip'] = ip
        info['mac'] = mac
        return info

    def getClientInfo(self, ip, mac):
        info = dict()
        device = models.Clients.objects.get(MAC_Address=mac)
        if device.IP_Address != ip:
            device.IP_Address = ip     
        device.save()

        try:
            coin_queue = models.CoinQueue.objects.get(Client=mac)
            total_coins = coin_queue.Total_Coins
        except ObjectDoesNotExist:
            total_coins = 0

        try:
            vouchers = models.Vouchers.objects.filter(Voucher_client=mac, Voucher_status='Not Used')

        except ObjectDoesNotExist:
            vouchers = None

        client = models.Clients.objects.get(MAC_Address=mac)
        status = client.Status

        if status == 'Connected':
            time_left = client.Expire_On - timezone.now()

        elif status == 'Disconnected':
            time_left = timedelta(0)

        elif status == 'Paused':
            time_left = device.Time_Left

        info['ip'] = ip
        info['mac'] = mac
        info['status'] = status
        info['time_left'] = int(timedelta.total_seconds(time_left))
        info['total_coins'] = total_coins
        info['vouchers'] = vouchers

        return info

    def getSettings(self):
        info = dict()
        settings = models.Settings.objects.get(pk=1)
        rate_type = settings.Rate_Type
        if rate_type == 'auto':
            base_rate = settings.Base_Value
            rates = models.Rates.objects.annotate(auto_rate=F('Denom')*int(base_rate.total_seconds())).values('Denom', 'auto_rate')
            info['rates'] = rates
        else:
            info['rates'] = models.Rates.objects.all()
        info['rate_type'] = rate_type
        info['hotspot'] = settings.Hotspot_Name
        info['slot_timeout'] = settings.Slot_Timeout
        info['background'] = settings.BG_Image
        info['voucher_flg'] = settings.Vouchers_Flg
        info['pause_resume_flg'] = settings.Pause_Resume_Flg
        info['redir_url'] = settings.Redir_Url

        return info

    def get(self, request, template_name=template_name):
        try:
            device_info = self.getDeviceInfo(request)
            ip = device_info['ip']
            mac = device_info['mac']

            if models.Clients.objects.filter(MAC_Address=mac).exists():
                info = self.getClientInfo(ip, mac)
            else:
                try:

                    client = models.Clients()
                    client.IP_Address = ip
                    client.Device_Name = None
                    client.MAC_Address = mac
                    client.save()

                    info = self.getClientInfo(ip, mac)
                except Exception as e:
                    raise e

        except Exception as e:
            raise e

        try:
            settings = self.getSettings()

        except Exception as e:
            raise e

        info = {**settings, **info}
        slot = models.CoinSlot.objects.get(pk=1)
        slot.save()

        return render(request, template_name, context=info)


class Slot(View):

    def post(self, request):
        if request.is_ajax():
            mac = request.POST.get('mac')

            try:
                settings = models.Settings.objects.get(pk=1)
                timeout = settings.Slot_Timeout
                client = models.Clients.objects.get(MAC_Address=mac)

            except ObjectDoesNotExist as e:
                resp = api_response(500)

            else:
                try:
                    slot_info = models.CoinSlot.objects.get(pk=1, Client=mac)
                    slot_info.Last_Updated = timezone.now()
                    slot_info.save()

                    resp = api_response(200)

                except ObjectDoesNotExist:
                    slot_info = models.CoinSlot.objects.get(pk=1)
                    time_diff = timedelta.total_seconds(timezone.now()-slot_info.Last_Updated)
                    if timedelta(seconds=time_diff).total_seconds() > timeout:
                        slot_info.Client = mac
                        slot_info.Last_Updated = timezone.now()
                        slot_info.save()
                        resp = api_response(200)
                    else:
                        resp = api_response(600)
                
            return JsonResponse(resp, safe=False)
        else:
            return HttpResponseForbidden(request)


class Pay(View):
    def get(self, request):
        template_name = 'error.html'
        return render(request, template_name)

    def post(self, request):
        if request.is_ajax() and request.META['REMOTE_ADDR'] in local_ip:
            slot_id = request.POST.get('slot_id')
            identifier = request.POST.get('identifier')
            pulse = int(request.POST.get('pulse', 0))

            try:
                slot_info = models.CoinSlot.objects.get(id=slot_id)

            except ObjectDoesNotExist:
                resp = api_response(400)

            else:
                connected_client = slot_info.Client

                settings = models.Settings.objects.get(pk=1)
                rate_type = settings.Rate_Type
                base_rate = settings.Base_Value
                timeout = settings.Slot_Timeout
                time_diff = timedelta.total_seconds(timezone.now()-slot_info.Last_Updated)
                try:
                    rates = models.Rates.objects.get(Pulse=pulse)

                except ObjectDoesNotExist:
                    resp = api_response(900)

                else:
                    if connected_client and timedelta(seconds=time_diff).total_seconds() < timeout:
                        ledger = models.Ledger()
                        ledger.Client = connected_client
                        ledger.Denomination = rates.Denom
                        ledger.Slot_No = slot_id
                        ledger.save()

                        if rate_type == 'auto':
                            new_time = base_rate * rates.Denom
                        else:
                            new_time = rates.Minutes
                        q, _ = models.CoinQueue.objects.get_or_create(Client=connected_client)
                        q.Total_Coins += rates.Denom
                        q.Total_Time += new_time
                        q.save()

                        slot_info.Last_Updated = timezone.now()
                        slot_info.save()

                        resp = api_response(200)
                    else:
                        resp = api_response(300)

            return JsonResponse(resp, safe=False)
        else:
            return HttpResponseForbidden(request)


class Commit(View):
    def get(self, request):
        if not request.is_ajax():
            return HttpResponseForbidden(request)

        else:
            data = dict()
            client = request.GET.get('mac')
            settings = models.Settings.objects.get(pk=1)
            timeout = settings.Slot_Timeout

            slot = models.CoinSlot.objects.get(pk=1, Client=client)

            time_diff = timedelta.total_seconds(timezone.now()-slot.Last_Updated)
            if timedelta(seconds=time_diff).total_seconds() > timeout:
                data['Status'] = 'Available'
            else:
                data['Status'] = 'Not Available'

            try:
                queue = models.CoinQueue.objects.get(Client=client)
                data['Total_Coins'] = queue.Total_Coins
                data['Total_Time'] = queue.Total_Time.total_seconds()/60

            except ObjectDoesNotExist:
                data['Total_Coins'] = 0
                data['Total_Time'] = 0

            return JsonResponse(data)

class Browse(View):

    def get(self, request):
        if request.is_ajax():
            ip = request.GET.get('ip')
            mac = request.GET.get('mac')

            try:
                coin_queue = models.CoinQueue.objects.get(Client=mac)
                total_time = coin_queue.Total_Time
                coin_queue.delete()

                client = models.Clients.objects.get(MAC_Address=mac)
                client.Time_Left += total_time
                client.save()

                settings = models.Settings.objects.get(pk=1)
                timeout = settings.Slot_Timeout
                coin_slot = models.CoinSlot.objects.get(pk=1)
                coin_slot.Last_Updated = coin_slot.Last_Updated - timedelta(seconds=timeout)
                coin_slot.save()

                resp = api_response(200)
                resp['extra'] = total_time + client.Time_Left

            except ObjectDoesNotExist:
                resp = api_response(700)    

            return JsonResponse(data=resp)
        else:
            return HttpResponseForbidden(request)


class Pause(View):
    def get(self, request):
        if request.is_ajax():
            ip = request.GET.get('ip')
            mac = request.GET.get('mac')
            action = request.GET.get('action')

            try:
                client_info = models.Clients.objects.get(MAC_Address=mac)

                if action == 'pause':
                    client_info.Status = 'Paused'
                    client_info.save()
                    resp = api_response(200)
                    resp['description'] = 'Paused'

                elif action == 'resume':
                    client_info.Status = 'Connected'
                    client_info.save()
                    resp = api_response(200)
                    resp['description'] = 'Connected'
                else:
                    resp = api_response(700)

            except ObjectDoesNotExist:
                resp = api_response(800)

            return JsonResponse(data=resp)

        else:
            return HttpResponseForbidden(request)

class GenerateVoucher(View):
    def get(self, request):
        client = request.GET.get("mac")
        data = dict()
        if not client:
            data['status'] = 'Error. Invalid Action'

        try:
            queue = models.CoinQueue.objects.get(Client=client)
            total_coins = queue.Total_Coins
            total_time = queue.Total_Time
            
            voucher = models.Vouchers()
            voucher.Voucher_status = 'Not Used'
            voucher.Voucher_client = client
            voucher.Voucher_time_value = total_time
            voucher.save()

            queue.delete()

            coin_slot = models.CoinSlot.objects.get(pk=1)
            coin_slot.Client = None
            coin_slot.save()

            data['voucher_code'] = voucher.Voucher_code
            data['status'] = 'OK'

        except ObjectDoesNotExist:
            data['status'] = 'Error. No coin(s) inserted.'
            
        return JsonResponse(data)

class Redeem(View):

    def post(self, request):
        if request.is_ajax():
            data = dict()
            voucher_code = request.POST.get('voucher', None)
            mac = request.POST.get('mac', None)
            try:
                voucher = models.Vouchers.objects.get(Voucher_code=voucher_code, Voucher_status = 'Not Used')
                time_value = voucher.Voucher_time_value

                if voucher.Voucher_client != mac:
                    voucher.Voucher_client = mac

                try:
                    client = models.Clients.objects.get(MAC_Address=mac)
                    client.Time_Left += time_value
                    client.save()

                    voucher.Voucher_status = 'Used'
                    voucher.save()

                except ObjectDoesNotExist:
                    resp = api_response(800)

                resp = api_response(200)
                resp['voucher_code'] = voucher.Voucher_code
                resp['voucher_time'] = time_value

            except ObjectDoesNotExist:
                resp = api_response(110)

            return JsonResponse(resp)

        else:
            return HttpResponseForbidden(request)

class Control(View):
    template_name = 'control.html'

    def post(self, request):
        if request.is_ajax():
            response = None
            action = request.POST.get("action", None)
            if action:
                response = device(action)

            return JsonResponse(response)
        else:
            return HttpResponseForbidden(request)


    def get(self, request):
        serial_error = 'You obtained an unauthorized copy of the software. Wifi hotspot customizations is limited. Please contact seller.'
        action = request.GET.get("action", None)

        info = dict()

        if action == 'reset':
            models.Ledger.objects.all().delete()
        
        settings = models.Settings.objects.get(pk=1)
        try:
            ledger = models.Ledger.objects.all()
            sum_ledger = ledger.aggregate(denom=Sum('Denomination'))
            info['denom'] = sum_ledger['denom']
        except ObjectDoesNotExist:
            info['denom'] = 0

        
        users = models.Clients.objects.filter(Status='Connected')

        info['user_count'] = users.count()
        info['count'] = ledger.count()
        info['hotspot'] = settings.Hotspot_Name
        info['slot_timeout'] = settings.Slot_Timeout

        fp = fprint()

        try:
            device = models.Device.objects.get(pk=1)
            if fp['hash'] == device.Device_ID and device.Activation_Status == '#FFFFFF' or request.user.is_superuser:
                info['message'] = None
            else:
                messages.error(request, serial_error)
                info['message'] = serial_error
            return render(request, self.template_name, context=info)

        except ObjectDoesNotExist:
            return HttpResponse(serial_error)


class Sweep(View):

    def get(self, request):
        if request.is_ajax() and request.META['REMOTE_ADDR'] in local_ip:

            clients = models.Clients.objects.all()

            with transaction.atomic():
                for client in clients:
                    client.save()

            return JsonResponse(list(models.Clients.objects.all().values()), safe=False)
        else:
            return HttpResponseForbidden(request)


class RelayStat(View):

    def get(self, request):
        if request.is_ajax() and request.META['REMOTE_ADDR'] in local_ip:
            slot = models.CoinSlot.objects.get(pk=1)
            return JsonResponse(slot.Status, safe=False)
        else:
            return HttpResponseForbidden(request)

class Settings(View):

    def get(self, request):
        if request.is_ajax() and request.META['REMOTE_ADDR'] == '::1' in local_ip:
            settings = models.Settings.objects.values().get(pk=1)
            return JsonResponse(settings, safe=False)
        else:
            return HttpResponseForbidden(request)


class EloadPortal(View):
    template_name = 'eload_portal.html'
    def get(self, request, template_name=template_name):
        return render(request, template_name, context={})

