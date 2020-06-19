from cryptography.fernet import Fernet
from base64 import b64decode
from app import models
import rsa
import json

def fprint():
    snm = dict()
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                serial = line[10:26]
        f.close()

        eth0_mac = open("/sys/class/net/eth0/address").read().strip()

        snm['serial'] = serial
        snm['eth0_mac'] = eth0_mac
    except:
        return False
    return snm

def cc(ac=None):
    dev = models.Device.objects.get(pk=1)
    data = dev.Device_SN + dev.Ethernet_MAC
    pub_rsa = dev.pub_rsa
    p_key = rsa.PublicKey.load_pkcs1(pub_rsa, 'PEM')

    try:
        dev_id = b64decode(ac if ac else dev.Device_ID)
    except:
        return False
        
    try:
        rsa.verify(data.encode('utf-8'), dev_id, p_key)
    except rsa.VerificationError:
        return False
    else:
        return True

def grc():
    dev = models.Device.objects.get(pk=1)
    ca = dev.ca
    data = dict()
    data['serial'] = dev.Device_SN
    data['eth0_mac'] = dev.Ethernet_MAC
    f = Fernet(ca)
    data_byte = json.dumps(data).encode('utf-8')
    res = f.encrypt(data_byte)
    return res