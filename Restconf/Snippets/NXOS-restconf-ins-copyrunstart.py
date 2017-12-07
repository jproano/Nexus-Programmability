#!/bin/env python3

import argparse, requests, json, logging
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-12-01"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def copy_run_start(HOST, USER, PASS):
    # This function connects to the XML Manager of the device an sends a command to copy the running configuration to startup 
    # to ensure any previous RESTCONF or configuration session is completed the routine will sleep for 2 seconds before executing
    # and wait two seconds after sending the command. I did it this way since the startup config isnt exposed in yang (yet)
    # where a copy configuration would work. Port 22 or 830 should work for the xmlagent subsystem but left the port 22 as
    # that port should work regardless of the restconf service being activated on port 830.
    url="https://" + HOST + "/ins"
    myheaders={'content-type':'application/json-rpc'}
    payload=[
        {
            "jsonrpc": "2.0",
            "method": "cli_ascii",
            "params": {
            "cmd": "copy running-config startup-config",
            "version": 1
            },
            "id": 1
        }
    ]
    response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(USER,PASS), verify=False)
    print(str(response.status_code))
    return()
    
def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-restconf-ins-copyrunstart.py -H 10.1.1.1 -U admin -P password"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Copy Run->Start RESTONF')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='IP Address of the Device')
    parser.add_argument('-U', '--Username', type=str,  dest='Username', help='Username for RESTCONF Access')
    parser.add_argument('-P', '--Password', type=str,  dest='Password', help='Password for RESTCONF Access')
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
        user = input("Please Enter the Username for RESTCONF Device Access > ")

    if(args.Password):
        passwd = args.Password
    else:
        passwd = input("Please Enter the Password for RESTCONF Device Access > ")
    
    copy_run_start(ip,user,passwd)
    return()

if __name__ == "__main__":
	main()