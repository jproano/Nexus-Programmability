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

def check_user_yang(HOST, USER, PASS, NEWUSER):
    # This routine will connect to the NETCONF interface and check the new user against the existing user information. If a user is
    # matched then we will expect data in the RPC reply. The Filter is configured so that only a matching user (CaSe SenSetive) will
    # be returned vs all users. 
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # The filter Expression below searches the <System><userext-items><user-items><User-list><name> with the value provided by the main
        # function during runtime via switch or direct user input. 
        user_filter = '''
		<System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <userext-items>
                <user-items>
                    <User-list>
                        <name>''' + NEWUSER + '''</name>
                    </User-list>
                </user-items>
            </userext-items>
		</System>'''
        # Check existing configuration for the existance of the proposed new user
        res = device.get(('subtree', user_filter))
        # Uncomment the line below if its deisred for the XML repsonse to be pretty printed to stdout
        # print (xml_.to_xml(res.data_ele, pretty_print=True))
        # Grab the Etree Element from the response and attempt to search the XML. An existing user will have the following structure
        # returned in the RPC reply XML: <data><System><userext-items><user-items><User-list><name>TEXT VALUE</...> The [0]'s in the etree will search
        # through the structure of the XML to find that name value and compare it against the user being created. The try is there as there 
        # wont be this structure returned for a non existent user so we need handling of this condition to identify a new user vs an existing one.
        # Usernames ARE case sensitive in NX-OS so no need for nifty string comparison technicques. 
        xml_data = res.data_ele
        try:
            if(xml_data[0][0][0][0][0].text == NEWUSER):
                return(False)
        except:
            return(True)

def check_role_yang(HOST, USER, PASS, NEWROLE):
    # This routine will connect to the NETCONF interface and check the new user role against the existing role information. If a role is
    # matched then we will expect data in the RPC reply and the script will continue. The Filter is configured so that only a matching role
    # (CaSe SenSetive) will be returned. Since the role data is a pre-req to the creation of a user if no match is found the script will exit
    # from within this function. 
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        # The filter Expression below searches the <System><userext-items><role-items><Role-list><name> with the role value provided by the main
        # function during runtime via switch or direct user input. 
        user_filter = '''
		<System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
            <userext-items>
                <role-items>
                    <Role-list>
                        <name>''' + NEWROLE + '''</name>
                    </Role-list>
                </role-items>
            </userext-items>
		</System>'''
        # Check existing configuration for the existance of the proposed role assignment
        res = device.get(('subtree', user_filter))
        # Uncomment the line below if its deisred for the XML repsonse to be pretty printed to stdout
        # print (xml_.to_xml(res.data_ele, pretty_print=True))
        # Grab the Etree Element from the response and attempt to search the XML. An existing user will have the following structure
        # returned in the RPC reply XML: <System><userext-items><role-items><Role-list><name>Role VALUE</...> The [0]'s in the etree will search
        # through the structure of the XML to find that name value and compare it against the user being created. The try is there as there 
        # wont be this structure returned for a non existent user so we need handling of this condition to identify a new user vs an existing one.
        # Roles ARE case sensitive in NX-OS so no need for nifty string comparison technicques. 
        xml_data = res.data_ele
        try:
            if(xml_data[0][0][0][0][0].text == NEWROLE):
                return()
        except:
            exit("Desired role doesnt exist! - Pre-existing/Valid Role is needed for user assignment. Exiting without changes.")
    

def create_user_yang(HOST, USER, PASS, NEWUSER, NEWPASSWD, NEWROLE):
    # This routine will connect to the NETCONF interface and configure the new user based on the credentials provided. If a user was matched
    # its assumed we arrived here by means of the force command. The role existance should have passed prior to arriving at this routine.
    # The following characteristics will be set by this filter. Username, Password (Type0 on entry - will be hashed in the config), role.
    # This is effecivly the same command as "username juju password goodjuju role network-admin" in the CLI with juju being the NEWUSER variable
    # goodjuju being the NEWPASSWORD variable and the network-admin being the NEWROLE variable. The pwdEncryptType being set to 0 is required
    # during existing user overwrites. 
    with manager.connect(host=HOST, port=830, username=USER, password=PASS, hostkey_verify=False,device_params={'name':'nexus',"ssh_subsystem_name": "netconf"}, look_for_keys=False, allow_agent=False) as device:
        user_create = '''
        <config>
            <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <userext-items>
                    <user-items>
                        <User-list>
                            <name>''' + NEWUSER + '''</name>
                            <pwd>''' + NEWPASSWD + '''</pwd>
                            <pwdEncryptType>0</pwdEncryptType>
                            <userdomain-items>
                                <UserDomain-list>
                                    <name>all</name>
                                    <role-items>
                                        <UserRole-list>
                                            <name>''' + NEWROLE + '''</name>
                                        </UserRole-list>
                                    </role-items>
                                </UserDomain-list>
                            </userdomain-items>
                        </User-list>
                    </user-items>
                </userext-items>
            </System>
        </config>'''
        # Edit the Running Configuration and configure the user. NOTE: this will NOT save the running config to startup. So look at the other
        # snippets on how that is accomplished. 
        res = device.edit_config(target='running', config=user_create)
        # Looking for an RPC Reply. We could make this a TRY in the future for better error handling but a good positive confirmation that
        # the device at least processed the RPC request that was sent. 
        if(res.ok):
            print("User " + NEWUSER + " successfully created.")
    return()

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-ncclient-YANG-usercreate.py -H 10.1.1.1 -U admin -P password -NU newusername -NP newpassword -NR Role -F"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus User Create')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='IP Address of the Device')
    parser.add_argument('-U', '--Username', type=str,  dest='Username', help='Username for NETCONF/XMLAGENT Access')
    parser.add_argument('-P', '--Password', type=str,  dest='Password', help='Password for NETCONF/XMLAGENT Access')
    parser.add_argument('-NU', '--NewUsername', type=str,  dest='NewUsername', help='New Username Desired')
    parser.add_argument('-NP', '--NewPassword', type=str,  dest='NewPassword', help='New Password')
    parser.add_argument('-NR', '--NewRole', type=str,  dest='NewRole', help='Role for New user ex: network-admin')
    parser.add_argument('-D', '--Debug', action='store_true', default=False, dest='Debug', help='Enable Debugging')
    parser.add_argument('-F', '--Force', action='store_true', default=False, dest='Force', help='Force User Config over an Existing User')
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
    
    if(args.NewUsername):
        newuser = args.NewUsername
    else:
        newuser = input("Please Enter the New Username for creation > ")

    if(args.NewPassword):
        newpasswd = args.NewPassword
    else:
        newpasswd = input("Please Enter the New Password for creation > ")
   
    if(args.NewRole):
        newrole = args.NewRole
    else:
        newrole = input("Please Enter the New Role for creation > ")
    
    # Check if role types are acceptable for NX-OS
    check_role_yang(ip,user,passwd,newrole)
    # If Roles checked out check for an existing user with the same username that is being requested. The check_user_yang will return either
    # True which means we dont have a conflict / existing user or a False which means there is an existing user. 
    if (check_user_yang(ip,user,passwd,newuser)):
        # No Conflict. Good on Roles, create our User. 
        create_user_yang(ip,user,passwd,newuser,newpasswd,newrole)
    else:
        # We have an existing user. Check for Force Switch to overwrite the existing user config. If we have it.. then proceed If not then
        # pump out a message and make no changes.
        if(args.Force):
            create_user_yang(ip,user,passwd,newuser,newpasswd,newrole)
        else:
            print("Duplicate User - No Changes Made. Use the Force switch -F if you want to override the user info.")
    return()

if __name__ == "__main__":
	main()
