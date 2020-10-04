from django import forms
from app import models

class ClientsForm(forms.ModelForm):
	Time_Left= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))
	
	class Meta:
		model = models.Clients
		fields = '__all__'

class NetworkForm(forms.ModelForm):
	Server_IP= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))
	Netmask= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))
	DNS_1= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))
	DNS_2= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))
	
	class Meta:
		model = models.Network
		fields = '__all__'

class SettingsForm(forms.ModelForm):
	Base_Value= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))
	Disable_Pause_Time= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))

	class Meta:
		model = models.Settings
		fields = '__all__'