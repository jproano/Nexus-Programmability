#!/bin/env python3

import argparse, requests, json, time, logging, base64
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-12-05"
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
        return True
    else:
        return False

def check_interface_yang(HOST,USER,PASS,INTERFACEID):
    # This routine will connect via the RESTCONF interface and query the interface to check that the interface is
    # admin down (shutdown). If the interface is not Admin down then we will consider it a "provisioned" interface
    # Any number of additional checks could be made in place of admin down (Ex. OperStatus, TCAM Entries, etc).
    # Programatically this is an example of fields in the intf-items tree that can be looked at.
    
    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. Searching for specific interface details is an example of a Key where PhysIf-list= *ID 
    # in the yang model and the ID field is in the "eth###/###" format for the designated interface. Its also important that the /
    # in the Eth intformation get changed to html escape characters so the correct XPath is used.
    INTERFACEID = INTERFACEID.replace("/", "%2F")
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/intf-items/phys-items/PhysIf-list=' + INTERFACEID

    # Build Headers and use an HTTP get to retrieve all readable configuration elements. NOTE the content type an accept is yang.data+json
    http_headers = { 'content-type': 'application/yang.data+json', 'accept': 'application/yang.data+json', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("GET", url, headers= http_headers, verify=False)
    if(response.status_code == 200):
        responsedata = response.json()
        if(responsedata['PhysIf-list'][0]['adminSt'] == "down"):
            return True
        else:
            return False
    else:
        print("error unexpected result")
        return False

def configure_interface_yang(HOST,USER,PASS,INTERFACEID,VLANID,DESC):
    # This routine will connect to the RESTCONF interface of an NX device and configure a designated port. The designated
    # port will also have its description edited (DESC), Be set in access mode <mode>, have an access vlan configured (VLANID), and
    # have the relevent STP items configured such as spanning-tree port type edge [<mode>edge], and spanning-tree bpduguard enabled 
    # [<bpduguard>enable]. The Programatically cool part here is we are combining disparate XPaths in the same rest call and bringing
    # back the URL to the closest common denominator. In this case "System".
    int_update = '''
    <intf-items>
        <phys-items>
            <PhysIf-list>
                <id>'''+ INTERFACEID +'''</id>
                <layer>Layer2</layer>
                <mode>access</mode>
                <accessVlan>vlan-'''+ str(VLANID) + '''</accessVlan>
                <adminSt>up</adminSt>
                <descr>''' + str(DESC) + '''</descr>
            </PhysIf-list>
        </phys-items>
    </intf-items>
    <stp-items>
        <inst-items>
            <if-items>
                <If-list>
                    <id>'''+ INTERFACEID +'''</id>
                    <mode>edge</mode>
                    <bpduguard>enable</bpduguard>
                </If-list>
            </if-items> 
        </inst-items>
    </stp-items>'''

    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. Searching for specific interface details is an example of a Key where PhysIf-list= *ID 
    # in the yang model and the ID field is in the "eth###/###" format for the designated interface. Its also important that the /
    # in the Eth intformation get changed to html escape characters so the correct XPath is used.
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System'

    # Build Headers and use an HTTP PATCH to add/modify the STP info. NOTE: we are sending XML and acepting back JSON! 
    http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+json', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("PATCH", url, headers= http_headers, data=int_update, verify=False)
    if(response.status_code == 201 or 204):
        print("Interface " + str(INTERFACEID) + " successfully configured for L2 on VLAN: " + str(VLANID) + ".")
    else:
        print("Error in configuration routing.. something went wrong.")
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-restconf-yang-vlancreate.py -H 10.1.1.1 -U admin -P password -NV 2 -NN VLAN_NAME -VN 300300 -SP 4096 -NI"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Access Port Config RESTCONF YANG')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='IP Address of the Device')
    parser.add_argument('-U', '--Username', type=str,  dest='Username', help='Username for NETCONF/XMLAGENT Access')
    parser.add_argument('-P', '--Password', type=str,  dest='Password', help='Password for NETCONF/XMLAGENT Access')
    parser.add_argument('-I', '--Interface', type=str,  dest='Interface', help='Interface to be configured. Ex. eth1/1')
    parser.add_argument('-V', '--VlanAssignment', type=str,  dest='VlanAssignment', help='Vlan-ID to be assigned to the interface (must be an already existing VLAN')
    parser.add_argument('-D', '--InterfaceDesc', type=str,  dest='InterfaceDesc', help='Interface Description')
    parser.add_argument('-F', '--Force', action='store_true', default=False, dest='Force', help='Force Interface Config - Even with an online port')
    parser.add_argument('-d', '--Debug', action='store_true', default=False, dest='Debug', help='Enable Debugging')
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
    
    if(args.Interface):
        interf = args.Interface
    else:
        interf = input("Please Enter the Interface for configuration > ")
    
    if(args.VlanAssignment):
        vlanid = args.VlanAssignment
    else:
        vlanid = input("Please Enter the VlanID for the L2 interface > ")
   
    if(args.InterfaceDesc):
        desc = args.InterfaceDesc
    else:
        desc = input("Please Enter the Description for the " + interf + " interface > ")
    # The routine check VLAN should return True if the vlan exists or false if there is no VLAN with that ID
    if(check_vlan_yang(ip,user,passwd,vlanid)):
        # We have at least the L2 defined locally so lets check to be sure the interface is down or check for
        # the force switch.
        if(check_interface_yang(ip,user,passwd,interf) or args.Force):
            configure_interface_yang(ip,user,passwd,interf,vlanid,desc)
        else:
            print('Interface didnt pass pre-change checks - No Changes made')
    else:
        print('VLAN Doesnt Exist - No Changes made.')
    return()

if __name__ == "__main__":
	main()
