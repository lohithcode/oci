# oci
OCI-python SDK

Exploring the ways to boot strap the the Oracle Cloud Infracture using Python-SDK. This is very convenient and frees up using other provisioning tools such as Terraform and Ansible.

Attached is the working code and output which
-  spins up the single instance
-  gets object-storage limits
-  tears down resources.

What it does:
Create a VCN, subnet and instance. 
Launch an instance with specified values for simplicity and demonstration.
This script takes the following single argument:
  - The path to the public SSH key which can be used for SSHing into the instance for later use.
To access the instance, Internet Gateway and Routing rules need to be added which are not included in this script.
Resources created by the script will be removed when the script is done.

How to use:
 - Install OCI CLI and setup ~/.oci folder with config and keys for API authentication.
 - then run the oci_launch.py <path to your ssh public key>
 ```
    # python3 launch_oci.py ~/.ssh/mykey.pub
```
   
