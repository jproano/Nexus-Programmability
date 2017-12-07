#!/bin/env python3

import sys, os, warnings, time, argparse, logging
from ncclient import manager, operations, xml_, debug
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-11-20"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def copy_run_start(HOST, USER, PASS):
    # This function connects to the XML Manager of the device an sends a command to copy the running configuration to startup 
    # to ensure any previous NETCONF or configuration session is completed the routine will sleep for 2 seconds before executing
    # and wait two seconds after sending the command. I did it this way since the startup config isnt exposed in yang (yet)
    # where a copy configuration would work. Port 22 or 830 should work for the xmlagent subsystem but left the port 22 as
    # that port should work regardless of the netconf service being activated on port 830.
    time.sleep(2)
    with manager.connect(host=HOST, port=22, username=USER, password=PASS, device_params={'name':'nexus',"ssh_subsystem_name": "xmlagent"}, hostkey_verify=False, look_for_keys=False) as device:
        res = device.exec_command({'copy running-config startup-config'})
        if(res.ok):
            print ('Running Configuration Saved to Startup Successfully')
    return()
    

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-ncclient-XMLMGR-copyrunstart.py -H 10.1.1.1 -U admin -P password"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Copy Run/Start Config')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='IP Address of the Device')
    parser.add_argument('-U', '--Username', type=str,  dest='Username', help='Username for NETCONF/XMLAGENT Access')
    parser.add_argument('-P', '--Password', type=str,  dest='Password', help='Password for NETCONF/XMLAGENT Access')
    parser.add_argument('-D', '--Debug', action='store_true', default=False, dest='Debug', help='Enable Debugging')
    args = parser.parse_args()
    if(args.Debug):
        print("Debug Mode On")
        logging.basicConfig(level=logging.DEBUG)
    
    if(args.HostIP):
        ip = args.HostIP
    else:
        ip = input("Please Enter the IP Address or Hostname of your Device > ")
    
    if(args.Username):
        user = args.Username
    else:
        user = input("Please Enter the Username for NETCONF/XMLAGENT Device Access > ")

    if(args.Password):
        passwd = args.Password
    else:
        passwd = input("Please Enter the Password for NETCONF/XMLAGENT Device Access > ")
    
    copy_run_start(ip,user,passwd)
    return()

if __name__ == "__main__":
	main()
