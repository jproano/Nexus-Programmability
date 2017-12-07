#!/bin/env python3

import argparse, requests, json, time, logging, base64
# Fix input vs raw_input between Python 2.x and 3.x
try: input = raw_input
except NameError: pass

__author__ = "Joshua Proano"
__version__ = "0.1"
__date__ = "2017-12-06"
__email__ = "jproano@cisco.com"
__status__ = "Beta"

def check_user_yang(HOST, USER, PASS, NEWUSER):
    # This routine will connect to the RESTCONF interface and check the new user against the existing user information. If a user is
    # matched then we will expect data in the RPC reply. The Filter is configured so that only a matching user (CaSe SenSetive) will
    # be returned vs all users. 

    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. Searching for a VLAN is an example of a Key where User-List= *ID in the yang model.
    # and the ID field is in the "UserNaMe" string format for the designated vlan.
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/userext-items/user-items/User-list=' + str(NEWUSER)

    # Build Headers and use an HTTP get to retrieve all readable configuration elements. 
    http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+xml', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("GET", url, headers= http_headers, verify=False)
    # If the person exists, will get a 200 response code. If not will get a 204 reponse code (No-Content). 
    if(response.status_code == 200):
        return False
    else:
        return True

def check_role_yang(HOST, USER, PASS, NEWROLE):
    # This routine will connect to the RESTCONF interface and check the new user role against the existing role information. If a role is
    # matched then we will expect data in the RPC reply and the script will continue. The Filter is configured so that only a matching role
    # (CaSe SenSetive) will be returned. Since the role data is a pre-req to the creation of a user if no match is found the script will exit
    # from within this function. 

    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. Searching for a VLAN is an example of a Key where User-List= *ID in the yang model.
    # and the ID field is in the "UserNaMe" string format for the designated vlan.
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/userext-items/role-items/Role-list=' + str(NEWROLE)

    # Build Headers and use an HTTP get to retrieve all readable configuration elements. 
    http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+xml', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("GET", url, headers= http_headers, verify=False)
    # If the role exists, will get a 200 response code. If not will get a 204 reponse code (No-Content). 
    if(response.status_code == 200):
        return 
    else:
        exit("Desired role doesnt exist! - Pre-existing/Valid Role is needed for user assignment. Exiting without changes.")

def create_user_yang(HOST, USER, PASS, NEWUSER, NEWPASSWD, NEWROLE):
    # This routine will connect to the RESTCONF interface and configure the new user based on the credentials provided. If a user was matched
    # its assumed we arrived here by means of the force command. The role existance should have passed prior to arriving at this routine.
    # The following characteristics will be set by this filter. Username, Password (Type0 on entry - will be hashed in the config), role.
    # This is effecivly the same command as "username juju password goodjuju role network-admin" in the CLI with juju being the NEWUSER variable
    # goodjuju being the NEWPASSWORD variable and the network-admin being the NEWROLE variable. The pwdEncryptType being set to 0 is required
    # during existing user overwrites. 

    # Prep username and password as a B64 encoded ASCII string for use in the HTML header. Encoding and Decoding in the b64 module
    # are needed to make the function interoperable between Python2 and Python3
    user_creds = USER + ':' + PASS
    user_credsb64 = base64.b64encode(bytes(user_creds.encode('utf_8'))).decode('ascii')

    # Use Top Level XPath in the NX-OS-Device Yang model for tree retrieval. The syntax for the use of the YANG model
    # in NX is http(s)://HOST/restconf/data/<YANG MODEL>:XPath. The XPath is similar to the structure of a Netconf filter
    # but requires key values in certain containers and leafs for proper resolution. pyang can show the model in tree form
    # and where Key values are needed. Searching for a VLAN is an example of a Key where User-List= *ID in the yang model.
    # and the ID field is in the "UserNaMe" string format for the designated vlan.
    url = 'https://' + HOST + '/restconf/data/Cisco-NX-OS-device:System/userext-items/user-items'

    user_create = '''
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
    </User-list>'''

    # Build Headers and use an HTTP get to retrieve all readable configuration elements. 
    http_headers = { 'content-type': 'application/yang.data+xml', 'accept': 'application/yang.data+xml', 'authorization': 'Basic %s' % user_credsb64, 'cache-control': 'no-cache'}
    response = requests.request("PATCH", url, headers= http_headers, data=user_create, verify=False)
    # If the user patch operation is successful will get a 204 response code.
    if(response.status_code == 204):
        print("User " + NEWUSER + " successfully created/modified.")
        return 
    else:
        print("Something went wrong.. DOH!")
        return

def main():
    # Setup Arguments to be processed at runtime. This will prevent any stagnant settings 
    # Example syntax for runtime "python3 NXOS-restconf-yang-usercreate.py -H 10.1.1.1 -U admin -P password -NU newusername -NP newpassword -NR Role -F"
    # Parse Incomming Runtime Variables using argparse library
    parser = argparse.ArgumentParser(description='Nexus User Create RESTCONF')
    parser.add_argument('-H', '--HostIP', type=str, dest='HostIP', help='IP Address of the Device')
    parser.add_argument('-U', '--Username', type=str,  dest='Username', help='Username for RESTCONF Access')
    parser.add_argument('-P', '--Password', type=str,  dest='Password', help='Password for RESTCONF Access')
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
