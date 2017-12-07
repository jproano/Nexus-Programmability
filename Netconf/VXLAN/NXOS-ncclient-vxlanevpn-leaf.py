#!/bin/env python3

import sys, os, warnings, time, argparse, json
from ncclient import manager, operations, xml_, debug
import logging
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-11-25"
__email__ = "jproano@cisco.com"
__status__ = "Alpha - Work in Progress!!!"

# Structure and Framework for the VXLAN Program
# 1. Check Features to be sure they are enabled (feature_check & feature_enable)
# 2. Loopback allocations/designations for framework
#   - LO0 - BGP/IGP router ID as well as establishing BGP sessions between Spines
#   - LO1 - VTEP Addressing
#   - LO2 - Anycast RP configuration (NA for Leaf Nodes)
# 3. Underlay Options OSPF/ISIS/iBGP 
#   - Program Will initially support OSPF and will add ISIS and iBGP upon request
#   - OSPF connections will be P2P and Area 1-n. Will reserve Area 0 for border use.
#   - Underlay is hardcoded in the default VRF if a non-default VRF is desired that 
#     should be changed in the code.

def feature_check(HOST, USER, PASS):
    ###############################################################################################
    # This routine checks the running configuration of the device for the following features:
    # feature interface-vlan ! ifvlan-items
    # feature bgp ! bgp-items
    # feature ospf ! ospf-items
    # feature pim ! pim-items
    # feature vn-segment-vlan-based ! vnsegment-items
    # nv overlay evpn ! evpn-items
    # feature nv overlay ! nvo-items
    ################################################################################################
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus', "ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        vxlan_feature_check = '''
		<System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <fm-items>
                <ifvlan-items/>
                <bgp-items/>
                <ospf-items/>
                <pim-items/>
                <vnsegment-items/>
                <evpn-items/>
                <nvo-items/>
            </fm-items>
        </System>
        '''
        rcfeatures = device.get(('subtree', vxlan_feature_check))
        # print (xml_.to_xml(rcfeatures.data_ele, pretty_print=True))
        featurelist = rcfeatures.data_ele
        featuresforenablement = []
        for elem in featurelist.iter(tag='{http://cisco.com/ns/yang/cisco-nx-os-device}ifvlan-items'):
            try:
                if elem[0].tag == '{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt':
                    if str(elem[0].text) != 'enabled':
                        featuresforenablement.append('ifvlan')
            except:
                sys.exit("Features Unable to be checked, Terminating without further actions")
        
        for elem in featurelist.iter(tag='{http://cisco.com/ns/yang/cisco-nx-os-device}bgp-items'):
            try:
                if elem[0].tag == '{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt':
                    if str(elem[0].text) != 'enabled':
                        featuresforenablement.append('bgp')
            except:
                sys.exit("Features Unable to be checked, Terminating without further actions")
        
        for elem in featurelist.iter(tag='{http://cisco.com/ns/yang/cisco-nx-os-device}ospf-items'):
            try:
                if elem[0].tag == '{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt':
                    if str(elem[0].text) != 'enabled':
                        featuresforenablement.append('ospf')
            except:
                sys.exit("Features Unable to be checked, Terminating without further actions")
        
        for elem in featurelist.iter(tag='{http://cisco.com/ns/yang/cisco-nx-os-device}pim-items'):
            try:
                if elem[0].tag == '{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt':
                    if str(elem[0].text) != 'enabled':
                        featuresforenablement.append('pim')
            except:
                sys.exit("Features Unable to be checked, Terminating without further actions")

        for elem in featurelist.iter(tag='{http://cisco.com/ns/yang/cisco-nx-os-device}vnsegment-items'):
            try:
                if elem[0].tag == '{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt':
                    if str(elem[0].text) != 'enabled':
                        featuresforenablement.append('vnsegment')
            except:
                sys.exit("Features Unable to be checked, Terminating without further actions")

        for elem in featurelist.iter(tag='{http://cisco.com/ns/yang/cisco-nx-os-device}evpn-items'):
            try:
                if elem[0].tag == '{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt':
                    if str(elem[0].text) != 'enabled':
                        featuresforenablement.append('evpn')
            except:
                sys.exit("Features Unable to be checked, Terminating without further actions")

        for elem in featurelist.iter(tag='{http://cisco.com/ns/yang/cisco-nx-os-device}nvo-items'):
            try:
                if elem[0].tag == '{http://cisco.com/ns/yang/cisco-nx-os-device}adminSt':
                    if str(elem[0].text) != 'enabled':
                        featuresforenablement.append('nvo')
            except:
                sys.exit("Features Unable to be checked, Terminating without further actions")

        return featuresforenablement

def feature_enable(HOST, USER, PASS, FEATURELIST):
    ################################################################################################
    # This routine edits the running configuration of the device and enables the following features:
    # feature interface-vlan ! ifvlan-items
    # feature bgp ! bgp-items
    # feature ospf ! ospf-items
    # feature pim ! pim-items
    # feature vn-segment-vlan-based ! vnsegment-items
    # nv overlay evpn ! evpn-items
    # feature nv overlay ! nvo-items
    # Feature enablement is based on the list of features that where checked and found to be not
    # Active in the check routine.
    ################################################################################################
    
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Header
        vxlan_feature_update = '''
        <config>
	    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <fm-items>'''
        # Add Tags Based on features needed
        if 'ifvlan' in FEATURELIST:
            vxlan_feature_update = vxlan_feature_update + '''
                    <ifvlan-items>
                        <adminSt>enabled</adminSt>
                    </ifvlan-items>'''
        if 'bgp' in FEATURELIST:
            vxlan_feature_update = vxlan_feature_update + '''
                    <bgp-items>
                        <adminSt>enabled</adminSt>
                    </bgp-items>'''
        if 'ospf' in FEATURELIST:
            vxlan_feature_update = vxlan_feature_update + '''                    
                    <ospf-items>
                        <adminSt>enabled</adminSt>
                    </ospf-items>'''
        if 'pim' in FEATURELIST:
            vxlan_feature_update = vxlan_feature_update + '''
                    <pim-items>
                        <adminSt>enabled</adminSt>
                    </pim-items>'''
        if 'vnsegment' in FEATURELIST:
            vxlan_feature_update = vxlan_feature_update + '''
                    <vnsegment-items>
                        <adminSt>enabled</adminSt>
                    </vnsegment-items>'''
        if 'evpn' in FEATURELIST:
            vxlan_feature_update = vxlan_feature_update + '''
                    <evpn-items>
                        <adminSt>enabled</adminSt>
                    </evpn-items>'''
        if 'nvo' in FEATURELIST:
            vxlan_feature_update = vxlan_feature_update + '''
                    <nvo-items>
                        <adminSt>enabled</adminSt>
                    </nvo-items>'''
        # Footer
        vxlan_feature_update = vxlan_feature_update + '''
                </fm-items>
 	    </System>
        </config>'''
        # print vxlan_feature_update
        res = device.edit_config(target='running', config=vxlan_feature_update)
        if res.ok:
            # print("Features Configured")
            return True
        else:
            return False

def configure_underlay(HOST, USER, PASS, UL_Protocol, UL_Protocol_Area, UL_PhysList, UL_LoopList):
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Create a Loopback for the Underlay to be used as the Router ID ; Configure the Designated Ethernet Ports for L3 mode and assign IP addressing
        underlay_int_config = '''
        <config>
	        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <intf-items>
                    <lb-items>'''
        for key in UL_LoopList:
            underlay_int_config = underlay_int_config + '''
                        <LbRtdIf-list>
                            <id>''' + str(key) + '''</id>
                        </LbRtdIf-list>'''        
        underlay_int_config = underlay_int_config + '''
                    </lb-items>
                    <phys-items>'''
        for key in UL_PhysList:
            underlay_int_config = underlay_int_config + '''
                        <PhysIf-list>
                            <id>''' + str(key) + '''</id>
                            <accessVlan>vlan-1</accessVlan>
                            <mode>access</mode>
                            <mtu>9216</mtu>
                            <layer>Layer3</layer>
                            <descr>To Spine</descr>
                            <adminSt>up</adminSt>
                        </PhysIf-list>'''
        underlay_int_config = underlay_int_config + '''
                    </phys-items>
                </intf-items>
                <ipv4-items>
                    <inst-items>
                        <dom-items>
                            <Dom-list>
                            <name>default</name>
                                <if-items>'''
        for key in UL_LoopList:
            underlay_int_config = underlay_int_config + '''        
                                    <If-list>
                                        <id>''' + str(key) + '''</id>
                                        <addr-items>
                                            <Addr-list>
                                                <addr>''' + str(UL_LoopList[key]) + '''</addr>
                                            </Addr-list>
                                        </addr-items>
                                    </If-list>'''
        for key in UL_PhysList:
            underlay_int_config = underlay_int_config + '''
                                    <If-list>
                                        <id>''' + str(key) + '''</id>
                                        <addr-items>
                                            <Addr-list>
                                                <addr>''' + str(UL_PhysList[key]) + '''</addr>
                                            </Addr-list>
                                        </addr-items>
                                    </If-list>'''
        underlay_int_config = underlay_int_config + '''                            
                                </if-items>
                            </Dom-list>   
                        </dom-items>
                    </inst-items>
                </ipv4-items>
            </System>
        </config>
        '''
        # print underlay_int_config
        res = device.edit_config(target='running', config=underlay_int_config)
        if res.ok:
            print "Underlay Interfaces Configured"
            sleep 3
            device 
        # Create OSPF Instance Called Underlay. Attach to Loopback for router ID and the connections to the Spine
        underlay_rp_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <ospf-items>
                    <inst-items>
                        <Inst-list>
                            <name>underlay</name>
                                <dom-items>
                                    <Dom-list>
                                        <name>default</name>
                                        <rtrId> + RTRIDHERE + </rtrId>
                                    </Dom-list>
                                </dom-items>
                        </Inst-list>
                    </inst-items>
                    <if-items>
                        <InternalIf-list>
                            <id>eth1/1</id>
                            <area>0.0.0.1</area>
                            <instance>underlay</instance>
                            <nwT>p2p</nwT>
                        </InternalIf-list>
                        <InternalIf-list>
                            <id>eth1/2</id>
                            <area>0.0.0.1</area>
                            <instance>underlay</instance>
                            <nwT>p2p</nwT>
                        </InternalIf-list>
                        <InternalIf-list>
                            <id>lo0</id>
                            <area>0.0.0.1</area>
                            <instance>underlay</instance>
                        </InternalIf-list>
                    </if-items>      
                </ospf-items>
            </System>
        </config>'''
        #                             <instanceid>0</instanceid> was in the InternalIF List
        get_ospf_details = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <intf-items>
                <lb-items>
                    <LbRtdIf-list>
                        <id>lo0</id>
                    </LbRtdIf-list>
                </lb-items>
                <phys-items>
                    <PhysIf-list>
                        <id>eth1/1</id>
                    </PhysIf-list>
                    <PhysIf-list>
                        <id>eth1/2</id>
                    </PhysIf-list>
                </phys-items>
            </intf-items>
            <ospf-items>
            </ospf-items>
        </System>
        '''
        #time.sleep(5)
        #res2 = device.edit_config(target='running', config=underlay_rp_config)
        #time.sleep(5)
        # res3 = device.get(('subtree', get_ospf_details))
        # print (xml_.to_xml(res3.data_ele, pretty_print=True))

    return()

def config_mcast_underlay(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address):
    with manager.connect(host=HOST, port=PORT, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Configure PIM and Multicast Connectivity from Leaf to Spine on loopback and uplink ports
        underlay_mc_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <pim-items>
                    <inst-items>
                        <dom-items>
                        <Dom-list>
                            <name>default</name>
                            <staticrp-items>
                                <rp-items>
                                    <StaticRP-list>
                                        <addr>192.168.0.100/32</addr>
                                        <rpgrplist-items>
                                            <RPGrpList-list>
                                                <grpListName>224.0.0.0/4</grpListName>
                                                <bidir>false</bidir>
                                                <override>false</override>
                                            </RPGrpList-list>
                                        </rpgrplist-items>
                                    </StaticRP-list>
                                </rp-items>
                            </staticrp-items>
                            <if-items>
                                <If-list>
                                    <id>lo0</id>
                                    <pimSparseMode>true</pimSparseMode>
                                </If-list>
                                <If-list>
                                    <id>eth1/1</id>
                                    <pimSparseMode>true</pimSparseMode>
                                </If-list>
                                <If-list>
                                    <id>eth1/2</id>
                                    <pimSparseMode>true</pimSparseMode>
                                </If-list>
                            </if-items>
                        </Dom-list>
                        </dom-items>
                    </inst-items>
                </pim-items>
            </System>
        </config>'''

        get_mc_details = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <pim-items>
            </pim-items>
        </System>
        '''
        res = device.edit_config(target='running', config=underlay_mc_config)
        time.sleep(5)
        # res2 = device.get(('subtree', get_mc_details))
        # print (xml_.to_xml(res2.data_ele, pretty_print=True))
        # file = open('nxconfig_vxlan.xml','w') 
        # file.write(xml_.to_xml(res2.data_ele, pretty_print=True)) 
        # file.close() 
    return()

def create_l2fabric(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address):
    with manager.connect(host=HOST, port=PORT, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Configure PIM and Multicast Connectivity from Leaf to Spine on loopback and uplink ports
        fabric_vxlan_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <bd-items>
                    <bd-items>
                        <BD-list>
                            <fabEncap>vlan-141</fabEncap>
                            <name>L2-VNI-141-T1</name>
                            <mode>CE</mode>
                            <accEncap>vxlan-50141</accEncap>
                        </BD-list>
                    </bd-items>
                </bd-items>
                <stp-items>
                    <inst-items>
                        <vlan-items>
                            <Vlan-list>
                                <id>141</id>
                                <priority>4096</priority>
                            </Vlan-list>
                        </vlan-items> 
                    </inst-items>
                </stp-items>
            </System>
        </config>
        '''
        tenant_vxlan_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <inst-items>
                    <Inst-list>
                        <name>Tenant-1</name>
                        <encap>vxlan-50999</encap>
                        <dom-items>
                            <Dom-list>
                                <name>Tenant-1</name>
                                <rd>rd:unknown:0:0</rd>
                                <af-items>
                                    <DomAf-list>
                                        <type>ipv4-ucast</type>
                                        <ctrl-items>
                                            <AfCtrl-list>
                                                <type>ipv4-ucast</type>
                                                <rttp-items>
                                                <RttP-list>
                                                    <type>import</type>
                                                    <ent-items>
                                                        <RttEntry-list>
                                                            <rtt>route-target:unknown:0:0</rtt>
                                                        </RttEntry-list>
                                                    </ent-items>
                                                </RttP-list>
                                                <RttP-list>
                                                    <type>export</type>
                                                    <ent-items>
                                                        <RttEntry-list>
                                                            <rtt>route-target:unknown:0:0</rtt>
                                                        </RttEntry-list>
                                                    </ent-items>
                                                </RttP-list>
                                                </rttp-items>
                                            </AfCtrl-list>
                                             <AfCtrl-list>
                                                <type>l2vpn-evpn</type>
                                                <rttp-items>
                                                <RttP-list>
                                                    <type>import</type>
                                                    <ent-items>
                                                        <RttEntry-list>
                                                            <rtt>route-target:unknown:0:0</rtt>
                                                        </RttEntry-list>
                                                    </ent-items>
                                                </RttP-list>
                                                <RttP-list>
                                                    <type>export</type>
                                                    <ent-items>
                                                        <RttEntry-list>
                                                            <rtt>route-target:unknown:0:0</rtt>
                                                        </RttEntry-list>
                                                    </ent-items>
                                                </RttP-list>
                                                </rttp-items>
                                            </AfCtrl-list>
                                        </ctrl-items>
                                    </DomAf-list>
                                </af-items>
                            </Dom-list>
                        </dom-items>
                    </Inst-list>
                </inst-items>
                <hmm-items>
                <adminSt>enabled</adminSt>
                    <fwdinst-items>
                        <adminSt>enabled</adminSt>
                        <amac>0000.1111.2222</amac>
                    </fwdinst-items>
                </hmm-items>
            </System>
        </config>
        '''
        get_fabric_details = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <inst-items>
                <Inst-list>
                    <name>Tenant-1</name>
                </Inst-list>
            </inst-items>
        </System>
        '''
        res = device.edit_config(target='running', config=fabric_vxlan_config)
        time.sleep(5)
        res2 = device.edit_config(target='running', config=tenant_vxlan_config)
        #res3 = device.get(('subtree', get_fabric_details))
        #print (xml_.to_xml(res3.data_ele, pretty_print=True))
        #file = open('nxconfig_vxlan.xml','w') 
        #file.write(xml_.to_xml(res3.data_ele, pretty_print=True)) 
        #file.close() 
    return()

def create_l3fabric(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address):
    with manager.connect(host=HOST, port=PORT, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Configure PIM and Multicast Connectivity from Leaf to Spine on loopback and uplink ports
        fabric_l3vni_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <intf-items>
                    <svi-items>
                        <If-list>
                            <id>vlan999</id>
                            <adminSt>up</adminSt>
                            <rtvrfMbr-items>
                                <tDn>/System/Inst-list[mode='Tenant-1']</tDn>
                            </rtvrfMbr-items>
                        </If-list>
                    </svi-items>
                </intf-items>
                <ipv4-items>
                    <inst-items>
                        <dom-items>
                        <Dom-list>
                            <name>Tenant-1</name>
                            <if-items>
                                <If-list>
                                    <id>vlan999</id>
                                    <forward>enabled</forward>
                                </If-list>
                            </if-items>
                        </Dom-list>
                        </dom-items>
                    </inst-items>
                </ipv4-items>
            </System>
        </config>'''

        fabric_l2vni_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <intf-items>
                    <svi-items>
                        <If-list>
                            <id>vlan141</id>
                            <adminSt>up</adminSt>
                            <rtvrfMbr-items>
                                <tDn>/System/Inst-list[mode='Tenant-1']</tDn>
                            </rtvrfMbr-items>
                        </If-list>
                    </svi-items>
                </intf-items>
                <ipv4-items>
                    <inst-items>
                        <dom-items>
                        <Dom-list>
                            <name>Tenant-1</name>
                            <if-items>
                                <If-list>
                                    <id>vlan141</id>
                                    <addr-items>
                                        <Addr-list>
                                            <addr>172.21.141.1/24</addr>
                                        </Addr-list>
                                    </addr-items>
                                </If-list>
                            </if-items>
                        </Dom-list>
                        </dom-items>
                    </inst-items>
                </ipv4-items>
                <hmm-items>
                    <fwdinst-items>
                        <if-items>
                            <FwdIf-list>
                                <id>vlan141</id>
                                <mode>anycastGW</mode>
                            </FwdIf-list>
                        </if-items>
                    </fwdinst-items>
                </hmm-items>
                <icmpv4-items>
                    <inst-items>
                        <dom-items>
                            <Dom-list>
                                <name>Tenant-1</name>
                                <if-items>
                                    <If-list>
                                        <id>vlan141</id>
                                        <ctrl>port-unreachable</ctrl>
                                    </If-list>
                                </if-items>
                            </Dom-list>
                        </dom-items>
                    </inst-items>
                </icmpv4-items>
            </System>
        </config>'''

        overlay_tunnelint_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <eps-items>
                    <epId-items>
                        <Ep-list>
                            <epId>1</epId>
                            <hostReach>bgp</hostReach>
                            <sourceInterface>lo1</sourceInterface>
                            <nws-items>
                                <vni-items>
                                    <Nw-list>
                                        <vni>50140</vni>
                                        <mcastGroup>239.0.0.140</mcastGroup>
                                    </Nw-list>
                                    <Nw-list>
                                        <vni>50999</vni>
                                        <associateVrfFlag>true</associateVrfFlag>
                                    </Nw-list>
                                </vni-items>
                            </nws-items>
                        </Ep-list>
                    </epId-items>
                </eps-items>
            </System>
        </config>'''

        overlay_tunnelint_enable = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <eps-items>
                    <epId-items>
                        <Ep-list>
                            <epId>1</epId>
                            <adminSt>enabled</adminSt>
                        </Ep-list>
                    </epId-items>
                </eps-items>
            </System>
        </config>'''
        get_fabric_details = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
        </System>
        '''
        res = device.edit_config(target='running', config=fabric_l2vni_config)
        time.sleep(5)
        res2 = device.edit_config(target='running', config=fabric_l3vni_config)
        time.sleep(5)
        res3 = device.edit_config(target='running', config=overlay_tunnelint_config)
        time.sleep(5)
        res3a = device.edit_config(target='running', config=overlay_tunnelint_enable)
        # res4 = device.get(('subtree', get_fabric_details))
        # print (xml_.to_xml(res3.data_ele, pretty_print=True))
        # file = open('nxconfig_vxlan.xml','w') 
        # file.write(xml_.to_xml(res4.data_ele, pretty_print=True)) 
        # file.close() 
    return()

def create_evpn_ctrl(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address):
    with manager.connect(host=HOST, port=PORT, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # Configure PIM and Multicast Connectivity from Leaf to Spine on loopback and uplink ports
        evpn_bgp_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <bgp-items>
                    <inst-items>
                        <asn>65000</asn>
                        <dom-items>
                            <Dom-list>
                                <name>default</name>
                                <af-items>
                                    <DomAf-list>
                                        <type>ipv4-ucast</type>
                                    </DomAf-list>
                                </af-items>
                                <peer-items>
                                    <Peer-list>
                                        <addr>192.168.0.1</addr>
                                        <af-items>
                                            <PeerAf-list>
                                                <type>l2vpn-evpn</type>
                                                <sendComExt>enabled</sendComExt>
                                                <sendComStd>enabled</sendComStd>
                                            </PeerAf-list>
                                        </af-items>
                                        <asn>65000</asn>
                                        <srcIf>lo0</srcIf>
                                    </Peer-list>
                                </peer-items>
                                <rtrId>10.1.1.11</rtrId>
                            </Dom-list>
                        </dom-items>
                    </inst-items>
                </bgp-items>
            </System>
        </config>'''

        evpn_cp_config = '''
        <config>
		    <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <evpn-items>
                    <bdevi-items>
                        <BDEvi-list>
                            <encap>vxlan-50141</encap>
                            <name>vxlan-50141</name>
                            <rd>rd:unknown:0:0</rd>
                            <rttp-items>
                                <RttP-list>
                                    <type>import</type>
                                    <ent-items>
                                        <RttEntry-list>
                                            <rtt>route-target:unknown:0:0</rtt>
                                        </RttEntry-list>
                                    </ent-items>
                                </RttP-list>
                                <RttP-list>
                                    <type>export</type>
                                    <ent-items>
                                        <RttEntry-list>
                                            <rtt>route-target:unknown:0:0</rtt>
                                        </RttEntry-list>
                                    </ent-items>
                                </RttP-list>
                            </rttp-items>
                        </BDEvi-list>
                    </bdevi-items>
                </evpn-items>
            </System>
        </config>
        '''

        get_fabric_details = '''
        <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <bgp-items/>
            <evpn-items/>
        </System>
        '''
        res = device.edit_config(target='running', config=evpn_bgp_config)
        time.sleep(5)
        res2 = device.edit_config(target='running', config=evpn_cp_config)
        time.sleep(5)
        # res4 = device.get(('subtree', get_fabric_details))
        # print (xml_.to_xml(res4.data_ele, pretty_print=True))
        # file = open('nxconfig_vxlan.xml','w') 
        # file.write(xml_.to_xml(res4.data_ele, pretty_print=True)) 
        # file.close() 

    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-ncclient-vxlanevpn-leaf.py -h 10.1.1.1 -u admin -p password -f -ulp ospf -uli eth1/1 -ulip 192.168.100.1/24"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus Access Port Config')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='Management IP Address of the Device', required=True)
    parser.add_argument('-U', '--Username', type=str, dest='Username', help='Username for NETCONF/XMLAGENT Access', required=True)
    parser.add_argument('-P', '--Password', type=str, dest='Password', help='Password for NETCONF/XMLAGENT Access', required=True)
    parser.add_argument('-F', '--feature_enable', action='store_true', default=False, dest='FeatureON', help='Enable all Needed Features for NX-OS to Run VXLAN EVPN', required=False)
    parser.add_argument('-UL', '--underlay_config', action='store_true', default=False, dest='UnderlayConfigON', help='Configure Underlay', required=False)
    parser.add_argument('-ULP', '--underlayproto', type=str, dest='ULProto', help="Desired Underlay protocol -- NOTE Only 'ospf' is supported right now", required=False)
    parser.add_argument('-ULA', '--underlayArea', type=str, dest='ULArea', help='Underlay Area ID - ex 1 or 2 or 3', required=False)    
    parser.add_argument('-ULI', '--underlayPhys', type=json.loads, dest='ULPhysList', help='Underlay Physical Interfaces and IPs to Spines', required=False)
    parser.add_argument('-ULL', '--underlayLoop', type=json.loads, dest='ULLoopList', help='Underlay Logical Interfaces and IPs (LO0)', required=False)
    parser.add_argument('-D', '--Debug', action='store_true', default=False, dest='Debug', help='Enable Debugging')
    args = parser.parse_args()
    if(args.Debug):
        DebugON = True
        print("Debug Mode On")
        # Enable This for Super Debugging
        # logging.basicConfig(level=logging.DEBUG)
    else:
        DebugON = False

    if args.HostIP:
        Host = str(args.HostIP)
    else:
        Host = input("Please Enter the IP Address or Hostname of your Device > ")

    if args.Username:
        User = str(args.Username)
    else:
        User = input("Please Enter the Username that has NetConf access to your Device > ")

    if args.Password:
        Pwd = str(args.Password)
    else:
        Pwd = input("Please Enter the Password that has NetConf access to your Device > ")

    if(args.FeatureON):
        print("Enable Needed Features for VXLAN Node")
        featurelist = feature_check(Host, User, Pwd)
        if featurelist == []:
            print "All needed features are enabled."
        else:
            print 'enabling features'
            if(feature_enable(Host, User, Pwd, featurelist) == False):
                sys.exit("Features Unable to be configured, Terminating without further actions")
    else:
        # Features not set to be enabled, check that needed features are turned on.
        if feature_check(Host, User, Pwd) == []:
            print "features passed"
        else:
            print "feature check failed"

    if(args.UnderlayConfigON):
        if feature_check(Host, User, Pwd) == []:
            if args.ULProto:
                UL_Protocol = str(args.ULProto)
            else:
                UL_Protocol = input("Please Enter the desired Underlay Protocol of the device (put in OSPF here!) > ")
            
            if args.ULArea:
                UL_Protocol_Area = str(args.ULArea)
            else:
                UL_Protocol_Area = input("Please Enter the desired OSPF Area ID for the Pod > ")
            
            if args.ULPhysList:
                UL_PhysList = args.ULPhysList
            else:
                UL_PhysList = dict(input("Please enter the physical interface list of the L3 uplinks to the Spines w IPs Ex: '{\"eth1/1\":\"10.1.1.2/30\",\"eth1/2\":\"10.1.1.6/30\"}' > "))
            
            if args.ULLoopList:
                UL_LoopList = args.ULLoopList
            else:
                UL_LoopList = dict(input("Please enter the logical interface list of the RTRID IP Ex: '{\"lo0\":\"192.168.1.1/32\"}' "))
            
            if configure_underlay(Host, User, Pwd, UL_Protocol, UL_Protocol_Area, UL_PhysList, UL_LoopList):
                print "Underlay Configured"
            else:
                exit("Error Configuring Underlay - Exiting")
        else:
            exit("feature check failed unable to configure underlay")
        
    #PORT = 830
    #SpineULList = {'eth1/1' : '10.1.1.1/30','eth1/2' : '10.1.1.5/30', 'lo0' : '10.0.0.10/32'}
    #UL_RP_Address = '10.0.0.3'
    #UL_Protocol = 'OSPF'
    #UL_Protocol_AS = "Underlay"
    # Configure Underlay
    # configure_underlay(HOST, PORT, USER, PASS, SpineULList, UL_Protocol, UL_Protocol_Area)
    # Configure Multicast on Underlay
    # config_mcast_underlay(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address)
    # Configure Overlay Fabric
    # create_l2fabric(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address)
    # create_l3fabric(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address)
    # Configure EVPN Control Plane
    # create_evpn_ctrl(HOST, PORT, USER, PASS, SpineULList, UL_RP_Address)
    return()

if __name__ == "__main__":
    main()
    
