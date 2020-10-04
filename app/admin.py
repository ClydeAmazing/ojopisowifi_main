from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from app import models, forms
from app.opw import cc

def client_check(request):
    if request.user.is_superuser:
        return True
    else:
        return cc()


class Singleton(admin.ModelAdmin):
    change_form_template  = 'singleton_change_form.html'

    def get_urls(self):
        urls = super(Singleton, self).get_urls()
        model_name = self.model._meta.model_name
        self.model._meta.verbose_name_plural = self.model._meta.verbose_name
        url_name_prefix = '%(app_name)s_%(model_name)s' % {
            'app_name': self.model._meta.app_label,
            'model_name': model_name,
        }
        custom_urls = [
            path('',
                self.admin_site.admin_view(self.change_view),
                {'object_id': str(1)},
                name='%s_change' % url_name_prefix),
        ]
        return custom_urls + urls

    # def response_change(self, request, obj):
    #     msg = '%s changed successfully' % obj
    #     self.message_user(request, msg)
    #     return HttpResponseRedirect("../../")


class ClientsAdmin(admin.ModelAdmin):
    form = forms.ClientsForm
    list_display = ('IP_Address', 'MAC_Address', 'Device_Name', 'Connection_Status', 'Time_Left', 'running_time')
    readonly_fields = ('IP_Address', 'MAC_Address', 'Expire_On', 'Notification_ID', 'Notified_Flag', 'Date_Created')
    actions = ['Connect', 'Disconnect', 'Pause', 'Whitelist']

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Clients List'}
        return super(ClientsAdmin, self).changelist_view(request, extra_context=extra_context)

    def message_user(self, *args, **kwargs):
        pass

    def Connect(self, request, queryset):
        for obj in queryset:
            res = obj.Connect()
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if res:
                messages.add_message(request, messages.SUCCESS, 'Device {} is now connected.'. format(device_name))
            else:
                messages.add_message(request, messages.WARNING, 'Unable to connect device {}'. format(device_name))

    def Disconnect(self, request, queryset):
        for obj in queryset:
            res = obj.Disconnect()
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if res:
                messages.add_message(request, messages.SUCCESS, 'Device {} is now disconnected.'. format(device_name))
            else:
                messages.add_message(request, messages.WARNING, 'Device {} is already disconnected/paused.'. format(device_name))

    def Pause(self, request, queryset):
        for obj in queryset:
            res = obj.Pause()
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if res:
                messages.add_message(request, messages.SUCCESS, 'Device {} is now paused.'. format(device_name))
            else:
                messages.add_message(request, messages.WARNING, 'Device {} is already paused/disconnected.'. format(device_name))


    def Whitelist(self, request, queryset):      
        for obj in queryset:
            device, created = models.Whitelist.objects.get_or_create(MAC_Address=obj.MAC_Address, defaults={'Device_Name': obj.Device_Name})
            device_name = obj.MAC_Address if not obj.Device_Name else obj.Device_Name
            if created:
                messages.add_message(request, messages.SUCCESS, 'Device {} is sucessfully added to whitelisted devices'.format(device_name))
                obj.delete()
            else:
                messages.add_message(request, messages.WARNING, 'Device {} was already added on the whitelisted devices'.format(device_name))


class WhitelistAdmin(admin.ModelAdmin):
    list_display = ('MAC_Address', 'Device_Name')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Whitelisted Devices'}
        return super(WhitelistAdmin, self).changelist_view(request, extra_context=extra_context)


class CoinSlotAdmin(admin.ModelAdmin):
    list_display = ('Edit', 'Client', 'Last_Updated')

    # def has_add_permission(self, *args, **kwargs):
    #     return not models.CoinSlot.objects.exists()

    # def has_delete_permission(self, *args, **kwargs):
    #     return False


class LedgerAdmin(admin.ModelAdmin):
    list_display = ('Date', 'Client', 'Denomination', 'Slot_No')
    list_filter = ('Client', 'Date')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Transaction Ledger'}
        return super(LedgerAdmin, self).changelist_view(request, extra_context=extra_context)


class SettingsAdmin(Singleton, admin.ModelAdmin):
    form = forms.SettingsForm
    list_display = ('Hotspot_Name', 'Hotspot_Address', 'Slot_Timeout', 'Rate_Type', 'Base_Value', 'Inactive_Timeout', 'Coinslot_Pin', 'Light_Pin')
    readonly_fields = ('background_preview',)
    
    def background_preview(self, obj):
        return obj.background_preview

    background_preview.short_description = 'Background Preview'
    background_preview.allow_tags = True

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

    def message_user(self, *args): # overridden method
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Wifi Settings updated successfully.')
        super(SettingsAdmin, self).save_model(request, obj, form, change)


class NetworkAdmin(Singleton, admin.ModelAdmin):
    form = forms.NetworkForm
    list_display = ('Edit', 'Upload_Rate', 'Download_Rate')
    # list_editable = ('Upload_Rate', 'Download_Rate')

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

    def message_user(self, *args): # overridden method
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Global Network Settings updated successfully.')
        super(NetworkAdmin, self).save_model(request, obj, form, change)


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


class DeviceAdmin(Singleton, admin.ModelAdmin):
    list_display = ('Device_SN', 'Ethernet_MAC')

    def has_add_permission(self, *args, **kwargs):
        return not models.Device.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def message_user(self, *args): # overridden method
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Hardware Settings updated successfully.')
        super(DeviceAdmin, self).save_model(request, obj, form, change)

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

class PushNotificationsAdmin(Singleton, admin.ModelAdmin):
    list_display = ('Enabled', 'notification_title', 'notification_message', 'notification_trigger_time')

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Push Notifications Settings'}
        return super(PushNotificationsAdmin, self).changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, *args, **kwargs):
        return not models.PushNotifications.objects.exists()

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_view_permission(self, *args, **kwargs):
        return False

    def message_user(self, *args): # overridden method
        pass

    def save_model(self, request, obj, form, change):
        messages.add_message(request, messages.INFO, 'Push Notification Settings updated successfully.')
        super(PushNotificationsAdmin, self).save_model(request, obj, form, change)

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
admin.site.register(models.PushNotifications, PushNotificationsAdmin)

settings = models.Settings.objects.get(pk=1)
admin_name = settings.Hotspot_Name

admin.AdminSite.site_header = admin_name
admin.AdminSite.site_title = admin_name
