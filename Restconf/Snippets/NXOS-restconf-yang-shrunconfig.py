#!/bin/env python3

import argparse, requests, json, time, logging, base64
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-12-02"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def show_run_all_yang(HOST, USER, PASS):
    # This routine will sleep for 2 seconds to ensure any previous RESTCONF/XML sessions are cleaned up then will connect
    # via the RESTCONF/YANG interface and retrieve the full yang modeled configuration of the Nexus Device. A file will be created
    # with the hostname-<year><month><day>-<hour><minute><second>.xml format and the running configuration will be saved to
    # that log file. This routing allows for human readable differences to be compared or retrived during routines for audit
    # purposes. IMPORTANT: The netcnfctrl service has to be started for this to work!!
    time.sleep(2)

    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. 
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/'
 
    # Build Headers and use an HTTP get to retrieve all readable configuration elements. 
    http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+xml', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("GET", url, headers= http_headers, verify=False)

    # Save the RAW Config into a File derived from Host + TimeStamp of Run and save as log file type.
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename = HOST + "-" + timestr + ".xml"
    file = open(filename,'w')
    file.write(response.content.decode("ascii"))
    file.close()
    print("File saved to: " + filename) 
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-restconf-yang-shrunconfig.py -H 10.1.1.1 -U admin -P password"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Backup Running RESTCONF YANG')
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
    
    show_run_all_yang(ip,user,passwd)
    return()

if __name__ == "__main__":
	main()