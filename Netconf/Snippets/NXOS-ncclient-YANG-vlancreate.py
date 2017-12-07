#!/bin/env python3

import sys, os, warnings, time, logging, argparse
from ncclient import manager, operations, xml_, debug
from lxml import objectify, etree
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-11-21"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def check_vlan_yang(HOST, USER, PASS, NEWVLAN):
    # This routine will connect via the NETCONF interface and query the VLANs for a match against the VLAN ID to
    # be created. If the VLAN ID already exists we will return a false to the main routine. If the VLAN doesnt exist
    # a True value will be returned. 
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Will look at the Bridge Domain items to get the details on if the VLAN exists. The Brdige domain set is what
        # holds the VLAN details, name info, type, etc. 
        bd_filter = '''
		<System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <bd-items>
                <bd-items>
                    <BD-list>
                        <fabEncap>vlan-''' + str(NEWVLAN) + '''</fabEncap>
                    </BD-list>
                </bd-items>
            </bd-items>
		</System>'''
        # Get the VLAN data based on the filter above. If the VLAN doesnt exist the RPC reply should not contain any
        # data. If the VLAN does exist the RPC reply will have data and we can match on the fabEncap tag on the reply.
        res = device.get(('subtree', bd_filter))
        # print (xml_.to_xml(res.data_ele, pretty_print=True))
        xml_data = res.data_ele
        try:
            if(xml_data[0][0][0][0][0].text == ('vlan-' + str(NEWVLAN))):
                return(False)
        except:
            return(True)
        

def configure_vlan_yang(HOST, USER, PASS, NEWVLAN, NEWVLNAME, VNI, STPPRI):
    # This routine will connect to the NETCONF interface and configure the new vlan based on the credentials provided. If a vlan was matched
    # its assumed we should not arrive at this point. 
    # The following characteristics will be set by this filter. vlanID number, vlan name, vnsegmentID (for VXLAN), and the STP priority for 
    # the vlan. This is effecivly the same command set as "vlan xx; (in vlan config) name some_name ; vn-segment xxxx ; 
    # (Back at global) ; spanning-tree vlan xx priorit xxxx".
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Stitch together the XML request based on the requested VLAN ID (required). The optional components are
        # the VLAN Name, VXLAN vn-segment ID, and the STP priority. If those values exist they will be included
        # in the XML request. 
        vlan_update = '''
        <config>
            <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <bd-items>
                    <bd-items>
                        <BD-list>
                            <fabEncap>vlan-''' + str(NEWVLAN) + '''</fabEncap>'''
        if(NEWVLNAME):
            vlan_update = vlan_update + '''
                            <name>''' + str(NEWVLNAME) + '''</name>'''
        if(VNI):
            vlan_update = vlan_update + '''
                            <accEncap>vxlan-''' + str(VNI) + '''</accEncap>'''
        vlan_update = vlan_update + '''
                            <mode>CE</mode>
                        </BD-list>
                    </bd-items>
                </bd-items>'''
        if(STPPRI):
            vlan_update = vlan_update + '''
                <stp-items>
                    <inst-items>
                        <vlan-items>
                            <Vlan-list>
                                <id>''' + str(NEWVLAN) + '''</id>
                                <priority>''' + str(STPPRI) + '''</priority>
                            </Vlan-list>
                        </vlan-items> 
                    </inst-items>
                </stp-items>'''
        vlan_update = vlan_update + '''
            </System>
        </config>'''
        # If interested in seeing the completed request string to stdout uncomment out the line below.
        # print(vlan_update)
        # Edit the Running Configuration and configure the vlan. NOTE: this will NOT save the running config to startup. Look at the other
        # snippets on how that is accomplished. 
        res = device.edit_config(target='running', config=vlan_update)
        # Looking for an RPC Reply. We could make this a TRY in the future for better error handling but a good positive confirmation that
        # the device at least processed the RPC request that was sent. 
        if(res.ok):
            print("VLAN " + str(NEWVLAN) + " successfully created.")
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-ncclient-YANG-vlancreate.py -H 10.1.1.1 -U admin -P password -NV 2 -NN VLAN_NAME -VN 300300 -SP 4096 -NI"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus VLAN Config')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='IP Address of the Device')
    parser.add_argument('-U', '--Username', type=str,  dest='Username', help='Username for NETCONF/XMLAGENT Access')
    parser.add_argument('-P', '--Password', type=str,  dest='Password', help='Password for NETCONF/XMLAGENT Access')
    parser.add_argument('-NV', '--NewVlan', type=str,  dest='NewVlan', help='New VLAN ID Desired')
    parser.add_argument('-NN', '--NewVlanName', type=str,  dest='NewVlanName', help='Vlan Name for the New ID (Optional)')
    parser.add_argument('-VN', '--VNSegmentID', type=str,  dest='VxlanVNID', help='Overlay vn-segment ID (Optional)')
    parser.add_argument('-SP', '--STPPriority', type=str,  dest='StpPri', help='Spanning Tree Priority (Optional)')
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
        user = input("Please Enter the Username for NETCONF/XMLAGENT Device Access > ")

    if(args.Password):
        passwd = args.Password
    else:
        passwd = input("Please Enter the Password for NETCONF/XMLAGENT Device Access > ")
    
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
