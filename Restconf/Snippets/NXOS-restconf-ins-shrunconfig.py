#!/bin/env python3

import argparse, requests, json, time, logging
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-12-01"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def show_run_all_human(HOST, USER, PASS):
    # This routine will sleep for 10 seconds to ensure any previous RESTCONF sessions are cleaned up then will connect
    # via the XML Manager interface and retrieve the full running configuration of the Nexus Device. A file will be created
    # with the hostname-<year><month><day>-<hour><minute><second>.log format and the running configuration will be saved to
    # that log file. This routing allows for human readable differences to be compared or retrived during routines for audit
    # purposes. 
    time.sleep(10)
    # Connect to NX device via XML Manager Interface (Port 22) and execute a copy run to start
    url="https://" + HOST + "/ins"
    myheaders={'content-type':'application/json-rpc'}
    payload=[
        {
            "jsonrpc": "2.0",
            "method": "cli_ascii",
            "params": {
            "cmd": "show running-config",
            "version": 1
            },
            "id": 1
        }
    ]
    response = requests.post(url,data=json.dumps(payload), headers=myheaders, auth=(USER,PASS), verify=False).json()
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename = HOST + "-" + timestr + ".log"
    file = open(filename,'w') 
    file.write(response["result"]["msg"])
    file.close()
    print("File saved to: " + filename) 
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-restconf-ins-shrunconfig.py -H 10.1.1.1 -U admin -P password"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Backup Running RESTCONF')
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
    
    show_run_all_human(ip,user,passwd)
    return()

if __name__ == "__main__":
	main()
