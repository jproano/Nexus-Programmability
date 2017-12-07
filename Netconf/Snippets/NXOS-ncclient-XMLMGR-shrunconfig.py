#!/bin/env python3

import sys, os, warnings, time, argparse, logging, xml.dom.minidom
from ncclient import manager, operations, xml_, debug
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-11-20"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def show_run_all_human(HOST, USER, PASS):
    # This routine will sleep for 10 seconds to ensure any previous NETCONF/XML sessions are cleaned up then will connect
    # via the XML Manager interface and retrieve the full running configuration of the Nexus Device. A file will be created
    # with the hostname-<year><month><day>-<hour><minute><second>.log format and the running configuration will be saved to
    # that log file. This routing allows for human readable differences to be compared or retrived during routines for audit
    # purposes. 
    time.sleep(10)
        # Connect to NX device via XML Manager Interface (Port 22) and execute a copy run to start
    with manager.connect(host=HOST, port=22, username=USER, password=PASS, device_params={'name':'nexus',"ssh_subsystem_name": "xmlagent"}, hostkey_verify=False, look_for_keys=False) as device:
        res = device.exec_command({'show running-config all'})
        # If we received a successful RPC reply go into parsing.
        if(res.ok):
            # Parse the XML RPC Reply and Extract the Data Tag out of the reply to get the RAW config. 
            xml_doc = xml.dom.minidom.parseString(res.xml)
            runningconfig = xml_doc.getElementsByTagName('data')
            # If you want to see the data element without the debug uncomment the line below.
            # print(runningconfig[0].firstChild.nodeValue)
            # Save the RAW Config into a File derived from Host + TimeStamp of Run and save as log file type.
            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = HOST + "-" + timestr + ".log"
            file = open(filename,'w') 
            file.write(runningconfig[0].firstChild.nodeValue)
            file.close()
            print("File saved to: " + filename) 
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-ncclient-XMLMGR-shrunconfig.py -H 10.1.1.1 -U admin -P password"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Download Run Config')
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
    
    show_run_all_human(ip,user,passwd)
    return()

if __name__ == "__main__":
	main()
