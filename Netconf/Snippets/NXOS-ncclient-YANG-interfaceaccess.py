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
    # be created. If the VLAN ID already exists we will return a true to the main routine. If the VLAN doesnt exist
    # a false value will be returned. The VLAN needs to be defined before we can apply it to the interface.
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Lets see what we Can get looking at the Bridge Domain Yang Model for the configured VLANs. Also limiting to The encap (VLANID)
        # name and VLAN mode.
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
        # Send the RPC request via get and save the XML reply to res. Once Saved parse the data and see if there is
        # a Match for the VLAN.
        res = device.get(('subtree', bd_filter))
        # print (xml_.to_xml(res.data_ele, pretty_print=True))
        xml_data = res.data_ele
        try:
            if(xml_data[0][0][0][0][0].text == ('vlan-' + str(NEWVLAN))):
                return(True)
        except:
            return(False)

def check_interface_yang(HOST,USER,PASS,INTERFACEID):
    # This routine will connect via the NETCONF interface and query the interface to check that the interface is
    # admin down (shutdown). If the interface is not Admin down then we will consider it a "provisioned" interface
    # Any number of additional checks could be made in place of admin down (Ex. OperStatus, TCAM Entries, etc).
    # Programatically this is an example of fields in the intf-items tree that can be looked at.
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        int_filter = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <intf-items>
                <phys-items>
                    <PhysIf-list>
                        <id>''' + INTERFACEID + '''</id>   
                    </PhysIf-list>
                </phys-items>
            </intf-items>
        </System>
        '''
        # Send the RPC request via get and save the XML reply to res. Once Saved parse the data and see if there is
        # a Match for the admin state of the interface and that it is down == CLI equivalent to shutdown on the interface.
        res = device.get(('subtree', int_filter))
        print(xml_.to_xml(res.data_ele, pretty_print=True))
        xml_data = res.data_ele
        try:
            if(xml_data[0][0][0][0][0].text == INTERFACEID):
                if(xml_data[0][0][0][0][2].tag == "{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt"):
                    if(xml_data[0][0][0][0][2].text == "down"):
                        return(True)
                    else:
                        return(False)
                else:
                    return(False)
            else:
                return(False)
        except:
            print('Interface Doesnt Exist or Yang Model Changed')
            return(False)

def configure_interface_yang(HOST,USER,PASS,INTERFACEID,VLANID,DESC):
    # This routine will connect to the NETCONF interface of an NX device and configure a designated port. The designated
    # port will also have its description edited (DESC), Be set in access mode <mode>, have an access vlan configured (VLANID), and
    # have the relevent STP items configured such as spanning-tree port type edge [<mode>edge], and spanning-tree bpduguard enabled [<bpduguard>enable].
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Programamtically this configuration set also shows that elements from multiple "itmes" tree's in the yang model can be relevenat to a what
        # a human interface would be a single interface subtree as well as that multiple "items" can be configured at once in a single command set.
        int_update = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
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
                </stp-items>
 		    </System>
        </config>'''
        # Edit the running configuration of the device with the above filter. NOTE: this will not save the running configuration to
        # startup. See other snippets to add that routine into the code if needed.
        res = device.edit_config(target='running', config=int_update)
        if(res.ok):
            print("Interface " + str(INTERFACEID) + " successfully configured for L2 on VLAN: " + str(VLANID) + ".")
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-ncclient-YANG-interfaceaccess.py -H 10.1.1.1 -U admin -P password -I eth1/3 -V 23 -D 'Configured for Server XXXX' -F"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Access Port Config')
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
