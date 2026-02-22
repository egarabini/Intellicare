#!/usr/bin/env python3
"""SSH Helper for remote server management."""
import paramiko
import sys
import time

def ssh_exec(cmd, timeout=30):
    """Execute command on remote server and return output."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('161.97.141.186', port=22, username='root', password='Crazy57LB', timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    exit_code = stdout.channel.recv_exit_status()
    ssh.close()
    if out:
        print(out)
    if err:
        print(f"STDERR: {err}")
    if exit_code != 0:
        print(f"EXIT_CODE: {exit_code}")
    return out, err, exit_code

if __name__ == '__main__':
    cmd = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'echo ok'
    ssh_exec(cmd)
