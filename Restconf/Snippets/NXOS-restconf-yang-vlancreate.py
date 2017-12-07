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

def check_vlan_yang(HOST, USER, PASS, NEWVLAN):
    # This routine will connect via the RESTCONF interface and query the VLANs for a match against the VLAN ID to
    # be created. If the VLAN ID already exists we will return a false to the main routine. If the VLAN doesnt exist
    # a True value will be returned. 

    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. Searching for a VLAN is an example of a Key where BD-list= *ID in the yang model.
    # and the ID field is in the "vlan-###" format for the designated vlan.
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/bd-items/bd-items/BD-list=vlan-' + str(NEWVLAN)

    # Build Headers and use an HTTP get to retrieve all readable configuration elements. 
    http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+xml', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("GET", url, headers= http_headers, verify=False)
    # If the VLAN exists, will get a 200 response code. If not will get a 204 reponse code (No-Content)
    if(response.status_code == 200):
        return False
    else:
        return True
        

def configure_vlan_yang(HOST, USER, PASS, NEWVLAN, NEWVLNAME, VNI, STPPRI):
    # This routine will connect to the RESTCONF interface and configure the new vlan based on the credentials provided. If a vlan was matched
    # its assumed we should not arrive at this point. 
    # The following characteristics will be set by this filter. vlanID number, vlan name, vnsegmentID (for VXLAN), and the STP priority for 
    # the vlan. This is effecivly the same command set as "vlan xx; (in vlan config) name some_name ; vn-segment xxxx ; 
    # (Back at global) ; spanning-tree vlan xx priorit xxxx".

    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    vlan_update_body = '<BD-list>\n\t<fabEncap>vlan-' + str(NEWVLAN) + '</fabEncap>\n\t'
    if(NEWVLNAME):
        vlan_update_body = vlan_update_body + '<name>' + str(NEWVLNAME) + '</name>\n\t'
    if(VNI):
        vlan_update_body = vlan_update_body + '<accEncap>vxlan-' + str(VNI) + '</accEncap>\n\t'
    vlan_update_body = vlan_update_body + '<mode>CE</mode>\n</BD-list>'

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. Searching for a VLAN is an example of a Key where BD-list= *ID in the yang model.
    # and the ID field is in the "vlan-###" format for the designated vlan.
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/bd-items/bd-items'
    
    # Build Headers and use an HTTP PATCH to add the vlan. 
    http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+xml', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("PATCH", url, headers= http_headers, data=vlan_update_body, verify=False)
    
    # If the VLAN is created, will get a 201 response code, added a 204 reponse code (No-Content) in case the VLAN is modified.
    if(response.status_code == 201 or 204):
        print("Vlan " + str(NEWVLAN) + " created/modified.")
    else:
        print("Error recieved code: " + str(response.status_code) + "from server. Unexpected.")
    
    # Second call is to update the STP info. This could concivably be combined with the VLAN method and placed into a higher XPath
    # programatically it was desired to show additional XPath examples. 
    if(STPPRI):
        stp_update_body = '<Vlan-list>\n\t<id>' + str(NEWVLAN) + '</id>\n\t<priority>' + str(STPPRI) + '</priority>\n</Vlan-list>'
        url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/stp-items/inst-items/vlan-items'
        
        # Build Headers and use an HTTP PATCH to add/modify the STP info. 
        http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+xml', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
        response = requests.request("PATCH", url, headers= http_headers, data=stp_update_body, verify=False)
        
        # If the STP content is modified then we should expect a 204 no content response.. added 201 just in case.
        if(response.status_code == 201 or 204):
            print("STP for VLAN" + str(NEWVLAN) + " modified.")
        else:
            print("Error recieved code: " + str(response.status_code) + "from server. Unexpected.")
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-restconf-yang-vlancreate.py -H 10.1.1.1 -U admin -P password -NV 2 -NN VLAN_NAME -VN 300300 -SP 4096 -NI"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus VLAN Config RESTCONF YANG')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='IP Address of the Device')
    parser.add_argument('-U', '--Username', type=str,  dest='Username', help='Username for RESTCONF Access')
    parser.add_argument('-P', '--Password', type=str,  dest='Password', help='Password for RESTCONF Access')
    parser.add_argument('-NV', '--NewVlan', type=str,  dest='NewVlan', help='New VLAN ID Desired')
    parser.add_argument('-NN', '--NewVlanName', type=str,  dest='NewVlanName', help='Vlan Name for the New ID (Optional, Use NI mode to avoid prompt)')
    parser.add_argument('-VN', '--VNSegmentID', type=str,  dest='VxlanVNID', help='Overlay vn-segment ID (Optional, Use NI mode to avoid prompt)')
    parser.add_argument('-SP', '--STPPriority', type=str,  dest='StpPri', help='Spanning Tree Priority (Optional, Use NI mode to avoid prompt)')
    parser.add_argument('-NI', '--NonInteractive', action='store_false', default=True, dest='NonInteractive', help='Enable Non-Interactive Mode. Dont Prompt for Optional Input')
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
    
    if(args.NewVlan):
        newvlan = args.NewVlan
    else:
        newvlan = input("Please Enter the New VlanID for creation > ")
    # Check for Non-Interactive Flag. That will determin to ask for input in the absense of additional
    # input or just set optional variables to None for processing te subsequent functions. 
    if(args.NonInteractive):
        if(args.NewVlanName):
            newvlanname = args.NewVlanName
        else:
            newvlanname = input("Please Enter the New VLAN Name for creation (Enter for none) > ")
    
        if(args.VxlanVNID):
            newvnid = args.VxlanVNID
        else:
            newvnid = input("If an VXLAN overlay Please Enter the desired VNID (Or enter for none which will default to CE mode > ")
        
        if(args.StpPri):
            stppri = args.StpPri
        else:
            stppri = input("Enter Desired STP Priority for the new VLAN (Or press enter which will default existing config > ")
    else:
        if(args.NewVlanName):
            newvlanname = args.NewVlanName
        else:
            newvlanname = None
    
        if(args.VxlanVNID):
            newvnid = args.VxlanVNID
        else:
            newvnid = None
        
        if(args.StpPri):
            stppri = args.StpPri
        else:
            stppri = None
    # The routine check VLAN should return True if no conflict exists or false if there already is a VLAN with that ID
    if(check_vlan_yang(ip,user,passwd,newvlan)):
        configure_vlan_yang(ip,user,passwd,newvlan,newvlanname,newvnid,stppri)
    else:
        print('VLAN Already Exists - No Changes made.')
    return()

if __name__ == "__main__":
	main()
