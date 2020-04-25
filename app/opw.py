import os
import hashlib
import json
import paramiko
import subprocess
import codecs
import re

def ssh_open():
    host = '10.0.0.1'
    port = 22
    username = 'root'
    password = 'Clydeamazing24'

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username, password)

    return ssh

def exec_command(mac, action):
    ssh = None
    response = None
    try:
        ssh = ssh_open()
        ssh.exec_command('sudo ndsctl {} {}'.format(action, mac))
        response = 'SUCCESS'

    finally:
        if ssh:
            ssh.close()

    return response

def device(action):
    ssh = None
    response = None
    try:
        if action in ('reboot', 'poweroff'):
            ssh = ssh_open()
            ssh.exec_command('sudo ' + action)
            response = 'SUCCESS'

        if action == 'refresh':
            ssh = ssh_open()
            ssh.exec_command('sudo /programs/up_dn.sh')
            response = 'SUCCESS'

    finally:
        if ssh:
            ssh.close()

    return response

def mac_pool():
    ssh = None
    response = None
    cmd = 'sudo ndsctl status'

    try:
        ssh = ssh_open()
        stdin, stdout, stderr = ssh.exec_command(cmd)
        outlines = stdout.readlines()

        try:
            index = outlines.index('Trusted MAC addresses:\n')
            macs = []
            for i in outlines[index+1:-1]:
                mac = i.strip()
                macs.append(mac)

            response = macs
        except ValueError:
            response = None
    finally:
        if ssh:
            ssh.close()

    return response

def fprint():
    snm = dict()
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                serial = line[10:26]
        f.close()

        eth0_mac = open("/sys/class/net/eth0/address").read().strip()
        eth_stripped = re.sub(':', '', eth0_mac)
        chal = str.upper(codecs.encode(serial + eth_stripped, 'rot_13'))
        sn = serial + eth0_mac + 'clyde bahog lobot'
        hashed_sn = hashlib.sha256(str(sn).encode('utf-8')).hexdigest()

        snm['status'] = 'success'
        snm['serial'] = serial
        snm['eth0_mac'] = eth0_mac
        snm['hash'] = hashed_sn
        snm['chal'] = chal

    except:
        snm['status'] = "error"
    return snm
