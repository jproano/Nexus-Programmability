# The Nexus NETCONF Repository #

The Majority of the code snippets on this repository that are python based have been tested with both python 2 and 3. The netconf method used in the code with the ncclient library. 

Tools in this repo have the following prerequisites:
sys, os, warnings, time, ncclient, logging, xml.dom.minifom, xmltodict, argparse

It is important that you have these libraries installed and available to run the code.

For the nexus files code revisions of 7.0.3.I6 or I7 are the code bases where these scripts where tested on. 
Code version from 7.0(3)I5 and 7.0(3)F1 should interoperate with these examples. 

Experimenting was done at parsing the XML results using different methods. Check the individual programs for more details.
 
## NETCONF Snippets ##

### NXOS-ncclient-XMLMGR-copyrunstart.py

This function connects to the XML Manager of the device an sends a command to copy the running configuration to startup 

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-ncclient-XMLMGR-copyrunstart.py [-h] [-H HOSTIP] [-U USERNAME]
                                            [-P PASSWORD] [-D]

Nexus Copy Run/Start Config

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -D, --Debug           Enable Debugging
```

The program will print a success message if the result of the send command is successful.

### NXOS-ncclient-XMLMGR-shrunconfig.py

This routine will connect via the XML Manager interface and retrieve the full running configuration of the Nexus Device. A file will be created with the hostname-<year><month><day>-<hour><minute><second>.log format and the running configuration will be saved to that log file. This routing allows for human readable differences to be compared or retrived during routines for audit purposes.

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-ncclient-XMLMGR-shrunconfig.py [-h] [-H HOSTIP] [-U USERNAME]
                                           [-P PASSWORD] [-D]

Nexus Download Run Config

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -D, --Debug           Enable Debugging
```
A file will be created with the hostname-<year><month><day>-<hour><minute><second>.log

### NXOS-ncclient-YANG-interfaceaccess.py

This program is a combination of 3 functions that ultimately will configure an Ethernet port as a access switchport on a designated vlan. Configuration CLI equivalent to:

interface Eth1/1
  switchport
  switchport mode access
  switchport access vlan NN
  spanning-tree port type edge
  spanning-tree bpduguard enable
  no shutdown

Prior to configuring the interface the program will check for the existence of the desired VLAN in a function, as well as if the port is in an Admin Down "shutdown" state. This state could be modified to reflect the operational state vs admin state. But is designed to show a programatic check of the interface to ensure it a candidate to be provisioned.

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-ncclient-YANG-interfaceaccess.py [-h] [-H HOSTIP] [-U USERNAME]
                                             [-P PASSWORD] [-I INTERFACE]
                                             [-V VLANASSIGNMENT]
                                             [-D INTERFACEDESC] [-F] [-d]

Nexus Access Port Config

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -I INTERFACE, --Interface INTERFACE
                        Interface to be configured. Ex. eth1/1
  -V VLANASSIGNMENT, --VlanAssignment VLANASSIGNMENT
                        Vlan-ID to be assigned to the interface (must be an
                        already existing VLAN
  -D INTERFACEDESC, --InterfaceDesc INTERFACEDESC
                        Interface Description
  -F, --Force           Force Interface Config - Even with an online port
  -d, --Debug           Enable Debugging
```
Error conditions in the VLAN checks or Interface Checks will result in the program not configuring the interface. If the program successfully runs the output will be the program configured the interface on the specific VLAN

### NXOS-ncclient-YANG-shrunconfig.py

This routine will connect via the XML Manager interface and retrieve the full running configuration of the yang model Nexus Device. A file will be created with the hostname-<year><month><day>-<hour><minute><second>.xml format and the running configuration will be saved to that log file. This routing allows for human readable differences to be compared or retrived during routines for audit purposes.

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-ncclient-YANG-shrunconfig.py [-h] [-H HOSTIP] [-U USERNAME]
                                         [-P PASSWORD] [-D]

Nexus YANG Show Run Config

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -D, --Debug           Enable Debugging
```
A file will be created with the hostname-<year><month><day>-<hour><minute><second>.xml. This is a BIG output so file is way better than screen output.

### NXOS-ncclient-YANG-usercreate.py

The program retrieves credentials and a host that is the intended target for the new use as well as the new username, password, and role. The program will check if the desired role exists in the device. This is a mandartory requirement. If there is no match on the role then the program will exit with an error. If the role exists the program will next check if the desired new user exists in the system. If there is an existing user the force switch can be used at runtime to overwrite and existing user or the system wont proceed with the command. Finally the system will process the user creation if all checks are successful or if the force switch is used. NOTE: the force switch will not change the exit behavior of the role check.

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-ncclient-YANG-usercreate.py [-h] [-H HOSTIP] [-U USERNAME]
                                        [-P PASSWORD] [-NU NEWUSERNAME]
                                        [-NP NEWPASSWORD] [-NR NEWROLE] [-D]
                                        [-F]

Nexus User Create

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -NU NEWUSERNAME, --NewUsername NEWUSERNAME
                        New Username Desired
  -NP NEWPASSWORD, --NewPassword NEWPASSWORD
                        New Password
  -NR NEWROLE, --NewRole NEWROLE
                        Role for New user ex: network-admin
  -D, --Debug           Enable Debugging
  -F, --Force           Force User Config over an Existing User
```

### NXOS-ncclient-YANG-vlancreate.py

The program will take input of a hostname, access credentials, and desire new vlan ID, name (optional), and VXLAN id (optional), & STP priority (optional). The routines will check if there is a vlan already configured with the desired VLAN ID if there is the program will not affect changes. If there is no conflcit the program will create the VLAN based on the input. The non interactive switch can be used to bypass getting queried for values that are not mandatry. 

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-ncclient-YANG-vlancreate.py [-h] [-H HOSTIP] [-U USERNAME]
                                        [-P PASSWORD] [-NV NEWVLAN]
                                        [-NN NEWVLANNAME] [-VN VXLANVNID]
                                        [-SP STPPRI] [-NI] [-D]

Nexus VLAN Config

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -NV NEWVLAN, --NewVlan NEWVLAN
                        New VLAN ID Desired
  -NN NEWVLANNAME, --NewVlanName NEWVLANNAME
                        Vlan Name for the New ID (Optional)
  -VN VXLANVNID, --VNSegmentID VXLANVNID
                        Overlay vn-segment ID (Optional)
  -SP STPPRI, --STPPriority STPPRI
                        Spanning Tree Priority (Optional)
  -NI, --NonInteractive
                        Enable Non-Interactive Mode. Dont Prompt for Optional
                        Input
  -D, --Debug           Enable Debugging
```

## NETCONF Provisioning ##
These are more complete programs than the snippets section and are focused on port provisioning. These programs provide additional functions and checks and combine the snippets to provide a full process. Ex. Perform Pre-checks->Backup Config->Make Changes->Save Changes->Backup Post Change Config etc. 

### NXOS-Access-Port-Provision.py
This program will perform checks, backup configs, configure the access ports, save the configuration, and backup the post change config.

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-Access-Port-Provision.py [-h] -H HOSTIP -U USERNAME -P PASSWORD -I
                                     INTERFACE -V INTERFACEVLAN [-D]

Nexus Access Port Config

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -I INTERFACE, --Interface INTERFACE
                        Interface for Configuration
  -V INTERFACEVLAN, --InterfaceVLAN INTERFACEVLAN
                        Desired VLAN for Interface Memebership
  -D, --Debug           Enable Debugging
```
### NXOS-TrunkEdge-Port-Provision.py
This program will perform checks (more robust parsing on vlan ranges!), backup configs, configure the trunk ports, save the configuration, and backup the post change config. The checks will include all desired vlans are correctly configured on the switch. The config will also place the port into stp edge trunk mode. 

#### Usage

If you don't include optional elements on the command line you will be prompted with questions.

```
usage: NXOS-TrunkEdge-Port-Provision.py [-h] -H HOSTIP -U USERNAME -P PASSWORD
                                        -I INTERFACE -V INTERFACEVLAN [-D]

Nexus Trunk Port Config

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTIP, --HostIP HOSTIP
                        IP Address of the Device
  -U USERNAME, --Username USERNAME
                        Username for NETCONF/XMLAGENT Access
  -P PASSWORD, --Password PASSWORD
                        Password for NETCONF/XMLAGENT Access
  -I INTERFACE, --Interface INTERFACE
                        Interface for Configuration
  -V INTERFACEVLAN, --InterfaceVLAN INTERFACEVLAN
                        Desired VLAN for Interface Memebership
  -D, --Debug           Enable Debugging
```
