from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin, messages
from app import models
from app.opw import fprint

def client_check(request):
    if request.user.is_superuser:
        return True
    else:
        try:
            device = models.Device.objects.get(pk=1)
            fp = fprint()
            sn = str(fp['hash'])

            if sn == device.Device_ID and device.Activation_Status == '#FFFFFF':
                return True
            else:
                return False
        
        except ObjectDoesNotExist:
            return False


class ClientsAdmin(admin.ModelAdmin):
    list_display = ('IP_Address', 'MAC_Address', 'Device_Name', 'Status', 'Connected_On', 'remaining_time')
    readonly_fields = ('Connected_On', 'Expire_On', 'Last_Updated')
    list_filter = ('Status', )
    # list_editable = ('Status', 'Time_Left')


class CoinSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'Client', 'Last_Updated')

    def has_add_permission(self, *args, **kwargs):
        return not models.CoinSlot.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False


class LedgerAdmin(admin.ModelAdmin):
    list_display = ('Date', 'Client', 'Denomination', 'Slot_No')
    list_filter = ('Client', 'Date')


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('Hotspot_Name', 'Hotspot_Address', 'Slot_Timeout', 'Rate_Type', 'Base_Value', 'Inactive_Timeout', 'Coinslot_Pin', 'Light_Pin')

    def has_add_permission(self, *args, **kwargs):
        return not models.Settings.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res

class NetworkAdmin(admin.ModelAdmin):
    # list_display = ('p'Upload_Rate', 'Download_Rate')
    # list_editable = ('Upload_Rate', 'Download_Rate')

    def has_add_permission(self, *args, **kwargs):
        return not models.Network.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res


class CoinQueueAdmin(admin.ModelAdmin):
    list_display = ('Client', 'Total_Coins', 'Total_Time')


class RatesAdmin(admin.ModelAdmin):
    list_display = ('Denom', 'Pulse', 'Minutes')
    list_editable = ('Minutes', 'Pulse')
    readonly_fields = ('Denom', )
    field_order = ('Minutes', 'Denom')

    def has_module_permission(self, *args, **kwargs):
        settings = models.Settings.objects.get(pk=1)
        if settings.Rate_Type == 'manual':
            return  True
        else:
            return  False

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('Device_ID', 'Activation_Status')

    def has_add_permission(self, *args, **kwargs):
        return not models.Device.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

class VouchersAdmin(admin.ModelAdmin):
    list_display = ('Voucher_code', 'Voucher_status', 'Voucher_client', 'Voucher_create_date_time', 'Voucher_used_date_time', 'Voucher_time_value')
    readonly_fields = ('Voucher_code', 'Voucher_used_date_time')

    def has_module_permission(self, *args, **kwargs):
        settings = models.Settings.objects.get(pk=1)
        if settings.Vouchers_Flg:
            return True
        else:
            return False

admin.site.register(models.CoinSlot, CoinSlotAdmin)
admin.site.register(models.Clients, ClientsAdmin)
admin.site.register(models.Ledger, LedgerAdmin)
admin.site.register(models.CoinQueue, CoinQueueAdmin)
admin.site.register(models.Settings, SettingsAdmin)
admin.site.register(models.Network, NetworkAdmin)
admin.site.register(models.Rates, RatesAdmin)
admin.site.register(models.Device, DeviceAdmin)
admin.site.register(models.Vouchers, VouchersAdmin)

settings = models.Settings.objects.get(pk=1)
admin_name = settings.Hotspot_Name

admin.AdminSite.site_header = admin_name
admin.AdminSite.site_title = admin_name

