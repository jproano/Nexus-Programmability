#!/bin/env python3

import sys, os, warnings, time, logging, argparse
from ncclient import manager, operations, xml_, debug
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-11-20"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def show_run_all_yang(HOST, USER, PASS):
    # This routine will sleep for 10 seconds to ensure any previous NETCONF/XML sessions are cleaned up then will connect
    # via the NETCONF/YANG interface and retrieve the full yang modeled configuration of the Nexus Device. A file will be created
    # with the hostname-<year><month><day>-<hour><minute><second>.xml format and the running configuration will be saved to
    # that log file. This routing allows for human readable differences to be compared or retrived during routines for audit
    # purposes. IMPORTANT: The netcnfctrl service has to be started for this to work!!
    time.sleep(10)
    # Connect to NX device via NETCONF Interface (Port 830) and execute a copy run to start
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False, device_params={'name':'nexus', "ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Use Top Level Filter in the NX-OS-Device Yang model for tree retrieval.
        my_filter = '''
		<System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
		</System>'''
        # Use get vs get_config to retrieve all readable configuration elements. 
        res = device.get(('subtree', my_filter))
        if(res.ok):
            # If you want to see the data element without the debug uncomment the line below. Note: this is a HUGE amt of info!!!
            # print (xml_.to_xml(res.data_ele, pretty_print=True))
            # Save the RAW Config into a File derived from Host + TimeStamp of Run and save as log file type.
            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = HOST + "-" + timestr + ".xml"
            file = open(filename,'w') 
            file.write(xml_.to_xml(res.data_ele, pretty_print=True)) 
            file.close()
            print("File saved to: " + filename) 
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-ncclient-YANG-shrunconfig.py -H 10.1.1.1 -U admin -P password"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus YANG Show Run Config')
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
    
    show_run_all_yang(ip,user,passwd)
    return()

if __name__ == "__main__":
	main()
