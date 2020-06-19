from django.core.exceptions import ValidationError
from django.contrib import messages
from tracking_model import TrackingModelMixin
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.urls import reverse
import subprocess
import string, random
import os

class Clients(TrackingModelMixin, models.Model):
    TRACKED_FIELDS = ['Status', 'Time_Left']
    status_choices = (
        ('Connected', 'Connected'),
        ('Disconnected', 'Disconnected'),
        ('Paused', 'Paused')
    )

    IP_Address = models.CharField(max_length=15, verbose_name='IP')
    MAC_Address = models.CharField(max_length=255, verbose_name='MAC Address', unique=True)
    Device_Name = models.CharField(max_length=255, verbose_name='Device Name', null=True, blank=True)
    Status = models.CharField(max_length=255, default='Disconnected', choices=status_choices)
    Connected_On = models.DateTimeField(null=True, blank=True)
    Time_Left = models.DurationField(default=timezone.timedelta(minutes=0))
    Expire_On = models.DateTimeField(null=True, blank=True)
    Last_Updated = models.DateTimeField(default=timezone.now, null=True, blank=True)
    Upload_Rate = models.IntegerField(verbose_name='Upload Bandwidth', help_text='Specify client internet upload bandwidth in Kbps. No value = unlimited bandwidth', null=True, blank=True )
    Download_Rate = models.IntegerField(verbose_name='Download Bandwidth', help_text='Specify client internet download bandwidth in Kbps. No value = unlimited bandwidth', null=True, blank=True )

    @property
    def remaining_time(self):
        if self.Status == 'Paused':
            return self.Time_Left
        else:
            if self.Expire_On and self.Connected_On:
                remaining_time = self.Expire_On - timezone.now()
                return remaining_time
            else:
                return timedelta(0)

    def save(self, *args, **kwargs):

        if 'Status' in self.tracker.changed:
            prev_status = self.tracker.changed['Status']
            curr_status = self.Status

            if prev_status == 'Connected':
                if curr_status == 'Disconnected':
                    self.Time_Left = timedelta(0)
                    self.Expire_On = None
                    self.Connected_On = None

                elif curr_status == 'Paused':
                    if self.remaining_time <= timedelta(0):#
                        self.Status = 'Disconnected'
                        self.Time_Left = timedelta(0)
                        self.Expire_On = None
                        self.Connected_On = None
                    else:
                        self.Time_Left = self.remaining_time
                        self.Expire_On = timezone.now() + self.remaining_time
                        self.Connected_On = None

            if prev_status == 'Disconnected':
                if curr_status == 'Connected':
                    if self.Time_Left <= timedelta(0):
                        self.Status = 'Disconnected'
                        self.Time_Left = timedelta(0)
                        self.Expire_On = None
                        self.Connected_On = None

                    else:
                        self.Expire_On = timezone.now() + self.Time_Left
                        self.Connected_On = timezone.now()

                if curr_status == 'Paused':
                    if self.Time_Left <= timedelta(0):
                        self.Status = 'Disconnected'
                        self.Time_Left = timedelta(0)
                        self.Expire_On = None
                        self.Connected_On = None
                    else:
                        self.Expire_On = timezone.now() + self.Time_Left
                        self.Connected_On = None

            if prev_status == 'Paused':
                if curr_status == 'Disconnected':
                    self.Time_Left = timedelta(0)
                    self.Expire_On = None
                    self.Connected_On = None

                if curr_status == 'Connected':
                    if self.Time_Left <= timedelta(0):
                        self.Status = 'Disconnected'
                        self.Time_Left = timedelta(0)
                        self.Expire_On = None
                        self.Connected_On = None
                    else:
                        self.Expire_On = timezone.now() + self.Time_Left
                        self.Connected_On = timezone.now()

            self.Last_Updated = timezone.now()

        elif 'Time_Left' in self.tracker.changed:
            prev_time_left = self.tracker.changed['Time_Left']
            curr_time_left = self.Time_Left

            if prev_time_left > timedelta(0) and curr_time_left <= timedelta(0):
                self.Status = 'Disconnected'
                self.Time_Left = timedelta(0)
                self.Expire_On = None
                self.Connected_On = None

            elif prev_time_left <= timedelta(0) and curr_time_left > timedelta(0):
                self.Status = 'Connected'
                self.Expire_On = timezone.now() + self.Time_Left
                self.Connected_On = timezone.now()

            else:
                if self.Status == 'Connected':
                    self.Expire_On = timezone.now() + self.Time_Left

            self.Last_Updated = timezone.now()

        else:
            if self.Status == 'Connected':
                if self.remaining_time <= timedelta(0):
                    self.Status = 'Disconnected'
                    self.Time_Left = timedelta(0)
                    self.Expire_On = None
                    self.Connected_On = None
                    
                    self.Last_Updated = timezone.now()
                else:
                    self.Time_Left = self.remaining_time

            if self.Status == 'Disconnected':
                if self.Time_Left > timedelta(0):
                    self.Status = 'Connected'
                    self.Expire_On = timezone.now() + self.Time_Left
                    self.Connected_On = timezone.now()

                    self.Last_Updated = timezone.now()

        super(Clients, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return str(self.IP_Address) + ' | ' + str(self.MAC_Address)

class Whitelist(models.Model):
    MAC_Address = models.CharField(max_length=255, verbose_name='MAC', unique=True)
    Device_Name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Whitelisted Device'
        verbose_name_plural = 'Whitelisted Devices'

    def __str__(self):
        name =  self.MAC_Address if not self.Device_Name else self.Device_Name
        return 'Device: ' + name


class Ledger(models.Model):
    Date = models.DateTimeField()
    Client = models.CharField(max_length=50)
    Denomination = models.IntegerField()
    Slot_No = models.IntegerField()

    def save(self, *args, **kwargs):
        self.Date = timezone.now()
        super(Ledger, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Ledger'
        verbose_name_plural = 'Ledger'

    def __str__(self):
        return 'Transaction no: ' + str(self.pk)


class CoinSlot(models.Model):
    Client = models.CharField(max_length=17, null=True, blank=True)
    Last_Updated = models.DateTimeField()
    Slot_ID = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'Coin Slot'
        verbose_name_plural = 'Coin Slot'

    def __str__(self):

        return 'Slot no: ' + str(self.pk)

class Rates(models.Model):
    Edit = "Edit"
    Denom = models.IntegerField(verbose_name='Denomination', help_text="Coin denomination corresponding to specified coinslot pulse.")
    Pulse = models.IntegerField(help_text="Coinslot pulse count. Don't change this if you dont know what you're doing")
    Minutes = models.DurationField(verbose_name='Duration', help_text='Internet access duration in hh:mm:ss format')

    class Meta:
        verbose_name = "Rate"
        verbose_name_plural = "Rates"

    def __str__(self):
        return 'Rates'


class CoinQueue(models.Model):
    Client = models.CharField(max_length=15, null=True, blank=True)
    Total_Coins = models.IntegerField(null=True, blank=True, default=0)
    Total_Time = models.DurationField(null=True, blank=True, default=timedelta())

    class Meta:
        verbose_name = 'Coin Queue'
        verbose_name_plural = 'Coin Queue'

    def __str__(self):
        if self.Client:
            return 'Coin queue for: ' + self.Client
        else:
            return 'Record'


class Settings(models.Model):
    rate_type_choices = (
        ('auto', 'Minutes/Peso'),
        ('manual', 'Custom Rate'),
    )
    enable_disable_choices = (
        (1, 'Enable'),
        (0, 'Disable'),
    )

    def get_image_path(instance, filename):
        return os.path.join(str(instance.id), filename)

    Hotspot_Name = models.CharField(max_length=255)
    Hotspot_Address = models.CharField(max_length=255, null=True, blank=True)
    BG_Image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    Slot_Timeout = models.IntegerField(help_text='Slot timeout in seconds.')
    Rate_Type = models.CharField(max_length=25, default="auto", choices=rate_type_choices, help_text='Select "Minutes/Peso" to use  Minutes / Peso value, else use "Custom Rate" to manually setup Rates based on coin value.')
    Base_Value = models.DurationField(default=timedelta(), verbose_name='Minutes / Peso')
    Inactive_Timeout = models.IntegerField(verbose_name='Inactive Timeout', help_text='Timeout before an idle client (status = Disconnected) is removed from the client list. (Minutes)')
    Redir_Url = models.CharField(max_length=255, verbose_name='Redirect URL', help_text='Redirect url after a successful login. If not set, will default to the timer page.', null=True, blank=True)
    Vouchers_Flg = models.IntegerField(verbose_name='Vouchers', default=1, choices=enable_disable_choices, help_text='Enables voucher module')
    Pause_Resume_Flg = models.IntegerField(verbose_name='Pause/Resume', default=1, choices=enable_disable_choices, help_text='Enables pause/resume function')
    Coinslot_Pin = models.IntegerField(verbose_name='Coinslot Pin', help_text='Please refer raspberry/orange pi GPIO.BOARD pinout.', null=True, blank=True)
    Light_Pin = models.IntegerField(verbose_name='Light Pin', help_text='Please refer raspberry/orange pi GPIO.BOARD pinout.', null=True, blank=True)
    

    def clean(self, *args, **kwargs):
        if self.Coinslot_Pin or self.Light_Pin:
            if self.Coinslot_Pin == self.Light_Pin:
                raise ValidationError('Coinslot Pin should not be the same as Light Pin.')

    class Meta:
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return 'Details'

class Network(models.Model):
    Upload_Rate = models.IntegerField(verbose_name='Upload Bandwidth', help_text='Specify global internet upload bandwidth in Kbps. No value = unlimited bandwidth', null=True, blank=True )
    Download_Rate = models.IntegerField(verbose_name='Download Bandwidth', help_text='Specify global internet download bandwidth in Kbps. No value = unlimited bandwidth', null=True, blank=True )

    class Meta:
        verbose_name = 'Network'
        verbose_name_plural = 'Network'

    def __str__(self):
        return 'Bandwidth Settings'


class Vouchers(models.Model):
    status_choices = (
        ('Used', 'Used'),
        ('Not Used', 'Not Used'),
        ('Expired', 'Expired')
    )

    def generate_code(size=6):
        found = False
        random_code = None

        while not found:
            random_code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))
            count = Vouchers.objects.filter(Voucher_code=random_code).count()
            if count == 0:
                found = True

        return random_code

    Voucher_code = models.CharField(default=generate_code, max_length=20, null=False, blank=False, unique=True)
    Voucher_status = models.CharField(verbose_name='Status', max_length=25, choices=status_choices, default='Not Used', null=False, blank=False)
    Voucher_client = models.CharField(verbose_name='Client', max_length=50, null=True, blank=True, help_text="Voucher code user. * Optional")
    Voucher_create_date_time = models.DateTimeField(verbose_name='Created Date/Time', auto_now_add=True)
    Voucher_used_date_time = models.DateTimeField(verbose_name='Used Date/Time', null=True, blank=True)
    Voucher_time_value = models.DurationField(verbose_name='Time Value', null=True, blank=True, help_text='Time value in minutes.')

    def save(self, *args, **kwargs):
        if self.Voucher_status == 'Used':
             self.Voucher_used_date_time = timezone.now()

        if self.Voucher_status == 'Not Used':
            self.Voucher_used_date_time = None

        super(Vouchers, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Voucher'
        verbose_name_plural = 'Vouchers'

    def __str__(self):
        return 'Voucher ' + self.Voucher_code


class Device(models.Model):
    Device_ID = models.CharField(max_length=255, null=True, blank=True)
    Ethernet_MAC = models.CharField(max_length=50, null=True, blank=True)
    Device_SN = models.CharField(max_length=50, null=True, blank=True)
    pub_rsa = models.TextField(null=False, blank=False)
    ca = models.CharField(max_length=200, unique=True, null=False, blank=False)
    action = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Device'
        verbose_name_plural = 'Device'

    def __str__(self):
        return 'xxx'