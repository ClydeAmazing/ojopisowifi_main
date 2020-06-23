from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin, messages
from app import models
from app.opw import cc

def client_check(request):
    if request.user.is_superuser:
        return True
    else:
        return cc()


class ClientsAdmin(admin.ModelAdmin):
    list_display = ('IP_Address', 'MAC_Address', 'Device_Name', 'Status', 'Connected_On', 'remaining_time')
    readonly_fields = ('Connected_On', 'Expire_On', 'Last_Updated')
    list_filter = ('Status', )
    actions = ['whitelist_client', 'disconnect_client']

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Clients List'}
        return super(ClientsAdmin, self).changelist_view(request, extra_context=extra_context)

    def message_user(self, *args, **kwargs):
        pass

    def disconnect_client(self, request, queryset):
        for obj in queryset:
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if obj.Status == 'Connected':
                obj.Status = 'Disconnected'
                obj.save()
                messages.add_message(request, messages.SUCCESS, 'Device {} is now disconnected.'. format(device_name))
            else:
                messages.add_message(request, messages.INFO, 'Device {} is already disconnected.'. format(device_name))


    def whitelist_client(self, request, queryset):      
        for obj in queryset:
            device, created = models.Whitelist.objects.get_or_create(MAC_Address=obj.MAC_Address, defaults={'Device_Name': obj.Device_Name})
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if created:
                messages.add_message(request, messages.SUCCESS, 'Device {} is sucessfully added to whitelisted devices'.format(device_name))
                obj.delete()
            else:
                messages.add_message(request, messages.WARNING, 'Device {} was already added on the whitelisted devices'.format(device_name))


    whitelist_client.short_description = "Add selected devices to whitelisted clients"
    disconnect_client.short_description = "Disconnect selected devices"

class WhitelistAdmin(admin.ModelAdmin):
    list_display = ('MAC_Address', 'Device_Name')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Whitelisted Devices'}
        return super(WhitelistAdmin, self).changelist_view(request, extra_context=extra_context)


class CoinSlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'Client', 'Last_Updated')

    def has_add_permission(self, *args, **kwargs):
        return not models.CoinSlot.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False


class LedgerAdmin(admin.ModelAdmin):
    list_display = ('Date', 'Client', 'Denomination', 'Slot_No')
    list_filter = ('Client', 'Date')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Transaction Ledger'}
        return super(LedgerAdmin, self).changelist_view(request, extra_context=extra_context)


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('Hotspot_Name', 'Hotspot_Address', 'Slot_Timeout', 'Rate_Type', 'Base_Value', 'Inactive_Timeout', 'Coinslot_Pin', 'Light_Pin')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Wifi Settings'}
        return super(SettingsAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, *args, **kwargs):
        return not models.Settings.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        res = client_check(request)
        return res


class NetworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'Upload_Rate', 'Download_Rate')
    list_editable = ('Upload_Rate', 'Download_Rate')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Global Network Settings'}
        return super(NetworkAdmin, self).changelist_view(request, extra_context=extra_context)

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
    list_display = ('Edit', 'Denom', 'Pulse', 'Minutes')
    field_order = ('Minutes', 'Denom')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Wifi Custom Rates'}
        return super(RatesAdmin, self).changelist_view(request, extra_context=extra_context)

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
    list_display = ('Device_SN', 'Ethernet_MAC')

    def has_add_permission(self, *args, **kwargs):
        return not models.Device.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

class VouchersAdmin(admin.ModelAdmin):
    list_display = ('Voucher_code', 'Voucher_status', 'Voucher_client', 'Voucher_create_date_time', 'Voucher_used_date_time', 'Voucher_time_value')
    readonly_fields = ('Voucher_code', 'Voucher_used_date_time')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Wifi Vouchers'}
        return super(VouchersAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, *args, **kwargs):
        settings = models.Settings.objects.get(pk=1)
        if settings.Vouchers_Flg:
            return True
        else:
            return False

admin.site.register(models.CoinSlot, CoinSlotAdmin)
admin.site.register(models.Clients, ClientsAdmin)
admin.site.register(models.Whitelist, WhitelistAdmin)
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
