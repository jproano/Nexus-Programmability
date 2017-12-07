#!/usr/bin/env python3

import sys, os, warnings, time, argparse, logging, xml.dom.minidom, random
from ncclient import manager, operations, xml_, debug

__author__ = "Joshua Proano"
__version__ = "0.5"
__date__ = "2017-10-27"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

operation_id = random.randint(1,100000)

def nx_config_precheck(HOST, PORT, USER, PASS, INTERFACE, IFVLAN, DEBUGON):
    # This Routine connects to a Nexus Device and performs pre-check operations. These pre-check operations
    # validate that there are no conflicting elements to the port such as "its online" as well as 
    # order of operation checks like the desired VLAN that the port is to be assigned is created.
    # Why we do this.. If the VLAN doesnt exist the aplication of the VLAN on the access port 
    # will not happen correctly so thats why we want to run pre-checks.

    with manager.connect(host=HOST, port=PORT, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as m:
        # Check that desired VLAN Exists in the Device. If not the port wont go in the correct VLAN
        vlan_filter = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <bd-items>
                <bd-items>
                    <BD-list>
                        <fabEncap>vlan-''' + IFVLAN + '''</fabEncap>
                    </BD-list>
                </bd-items>
            </bd-items>
		</System>'''
        vlanres = m.res = m.get(('subtree', vlan_filter))
        if(DEBUGON):
            print (xml_.to_xml(vlanres.data_ele, pretty_print=True))
        xml_doc = xml.dom.minidom.parseString(vlanres.xml)
        VLAN_ID = xml_doc.getElementsByTagName('fabEncap')
        if not VLAN_ID:
            sys.exit("VLAN " + str(IFVLAN) + " Does not exist terminating without changes")
        if(DEBUGON):
            print("VLAN Check OK")

        # Check if Interface is currently UP.. if so this could be damaging
        int_filter = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <intf-items>
                <phys-items>
                    <PhysIf-list>
                        <id>''' + INTERFACE + '''</id>   
                    </PhysIf-list>
                </phys-items>
            </intf-items>
        </System>
        '''
        res = m.get(('subtree', int_filter))
        # print (xml_.to_xml(res.data_ele, pretty_print=True))
        xml_doc = xml.dom.minidom.parseString(res.xml)
        INT_UP = xml_doc.getElementsByTagName('operSt')
        if (INT_UP[0].firstChild.nodeValue == 'up'):
            sys.exit("Interface {INTERFACE} is UP! Terminating without changes")
        
        if(DEBUGON):
            print("Interface Check OK")
    return()

def nx_config_accessport(HOST, PORT, USER, PASS, INTERFACE, IFVLAN, DEBUGON):
    # This routine performs the changes via the yang module to a nexus device. This has been tested
    # on NX versions 7.0.3.I6 and 7.0.3.I7 code. The changes are specific to a single interface called
    # from the switch "ex eth1/3" and is designed to set the switchport command "layer2", set the 
    # access vlan to the vlan specified during runtime of the script "accessvlan", and enabling the port
    # by ensuring the admin state is "up" which effectivly is a no shutdown command. In addition the 
    # spanning tree is configured for port type edge, and bpdu guard is enabled. 
    with manager.connect(host=HOST, port=PORT, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        interface_data = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <intf-items>
                    <phys-items>
                        <PhysIf-list>
                            <id>''' + INTERFACE + '''</id>
                            <layer>Layer2</layer>
                            <accessVlan>vlan-''' + str(IFVLAN) + '''</accessVlan>
                            <adminSt>up</adminSt>
                        </PhysIf-list>
                    </phys-items>
                </intf-items>
                <stp-items>
                    <inst-items>
                        <if-items>
                            <If-list>
                                <id>''' + INTERFACE + '''</id>
                                <mode>edge</mode>
                                <bpduguard>enable</bpduguard>
                            </If-list>
                        </if-items> 
                    </inst-items>
                </stp-items>
 		    </System>
        </config>'''
        res = device.edit_config(target='running', config=interface_data)
        if(DEBUGON):
            print (str(res))
            #file = open('Modification.xml','w') 
            #file.write(str(res)) 
            #file.close()
            print("Config Changes Pushed")
    return()

def nx_config_backup_pre(HOST, USER, PASS, DEBUGON):
    # This routine uses the XML manager interface to get the human readable running configuration
    # of the system and save the confguration - pre change for backup purposes. One idea for this
    # is to also use this routine to backup the XML config using yang and be able to diff and roll-
    # back. For now this routine is primarily for pre-state backup. This command could also be changed
    # to a show run interface command to localize the specific interface changed. The whole run 
    # config was elected to ensure that the script wasnt doing anything it wasnt suppose to do for
    # the system.
    #  
    # Sleep for 10 Seconds just to be sure any check/config change sessions are complete within the NX device
    time.sleep(10)
    # Connect to NX device via XML Manager Interface (Port 22) and execute a show run and backup to file
    with manager.connect(host=HOST, port=22, username=USER, password=PASS, device_params={'name':'nexus'}, hostkey_verify=False, look_for_keys=False) as device:
        res = device.exec_command({'show running-config'})
        xml_doc = xml.dom.minidom.parseString(res.xml)
        runningconfig = xml_doc.getElementsByTagName('data')
        # print(runningconfig[0].firstChild.nodeValue)
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = HOST + "-OPPID" + str(operation_id) + "-" + timestr + "-preChange.log"
        file = open(filename,'w') 
        file.write(runningconfig[0].firstChild.nodeValue)
        file.close()
        if(DEBUGON):
            print ("PreChange File Written")
    return()

def nx_config_backup_post(HOST, USER, PASS, DEBUGON):
    # This routine uses the XML manager interface to get the human readable running configuration
    # of the system and save the confguration - prost change for backup/audit/diff purposes. 
    #
    # Sleep for 10 Seconds just to be sure any check/config change sessions are complete within the NX device
    time.sleep(10)
    # Connect to NX device via XML Manager Interface (Port 22) and execute a show run and backup to file
    with manager.connect(host=HOST, port=22, username=USER, password=PASS, device_params={'name':'nexus'}, hostkey_verify=False, look_for_keys=False) as device:
        res = device.exec_command({'show running-config'})
        xml_doc = xml.dom.minidom.parseString(res.xml)
        runningconfig = xml_doc.getElementsByTagName('data')
        # print(runningconfig[0].firstChild.nodeValue)
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = HOST + "-OPPID" + str(operation_id) + "-" + timestr + "-postChange.log"
        file = open(filename,'w') 
        file.write(runningconfig[0].firstChild.nodeValue)
        file.close()
        if(DEBUGON):
            print ("Post Change File Written")
    return()

def nx_config_wrme(HOST, PORT, USER, PASS, DEBUGON):
    # This routine access the XML Manager interface to write the running config to startup. This is done
    # in lieu of a traditional netconf copy_config since the startup config capapbility isnt yet exposed
    # to the netconf/yang interface.
    #   
    # Sleep for 10 Seconds just to be sure any configuration changes are complete within the NX device
    time.sleep(10)
    # Connect to NX device via XML Manager Interface (Port 22) and execute a copy run to start
    with manager.connect(host=HOST, port=PORT, username=USER, password=PASS, device_params={'name':'nexus'}, hostkey_verify=False, look_for_keys=False) as device:
        res = device.exec_command({'copy running-config startup-config'})
        time.sleep(10)
        if(DEBUGON):
            print ("Write Mem Command Submitted")
    return()

if __name__ == "__main__":
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-Access-Port-Provision.py -H 10.1.1.1 -U admin -P password -I eth1/1 -V 22"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Access Port Config')
    parser.add_argument('-H', '--HostIP', type=str, help='IP Address of the Device', required=True)
    parser.add_argument('-U', '--Username', type=str, help='Username for NETCONF/XMLAGENT Access', required=True)
    parser.add_argument('-P', '--Password', type=str, help='Password for NETCONF/XMLAGENT Access', required=True)
    parser.add_argument('-I', '--Interface', type=str, help='Interface for Configuration', required=True)
    parser.add_argument('-V', '--InterfaceVLAN', type=str, help='Desired VLAN for Interface Memebership', required=True)
    parser.add_argument('-D', '--Debug', action='store_true', default=False, dest='Debug', help='Enable Debugging')
    args = parser.parse_args()
    if(args.Debug):
        DebugON = True
        print("Debug Mode On")
        # Enable This for Super Debugging
        # logging.basicConfig(level=logging.DEBUG)
    else:
        DebugON = False
    # Perform Interface and VLAN Pre-Checks
    nx_config_precheck(args.HostIP,830,args.Username,args.Password,args.Interface,args.InterfaceVLAN,DebugON)
    # Connect to Device and Backup Raw config - Pre-Change
    nx_config_backup_pre(args.HostIP,args.Username,args.Password,DebugON)
    # Connect to the Yang Interface to Modify configuration
    nx_config_accessport(args.HostIP,830,args.Username,args.Password,args.Interface,args.InterfaceVLAN,DebugON)
    # Connect to the XML Agent Interface to Save Configuration
    nx_config_wrme(args.HostIP,22,args.Username,args.Password,DebugON)
    # Connect to Device and Backup Raw config and Yang Config - Post-Change
    nx_config_backup_post(args.HostIP,args.Username,args.Password,DebugON)