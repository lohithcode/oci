# coding: utf-8
# OCI - Take home Assignment
#   * Create a VCN, subnet and instance. 
#   * Launch an instance with specified values for simplicity and demonstration.
#
# This script takes the following single argument:
#   * The path to the public SSH key which can be used for SSHing into the instance for later use.
#   * To access the instance, Internet Gateway and Routing rules need to be added which are not included in this script.
#
# Resources created by the script will be removed when the script is done.

import oci
import os.path
import sys


AVAILABILTY_DOMAIN= "ZMvy:US-ASHBURN-AD-2"
SHAPE = "VM.Standard.E2.1.Micro"
IMAGE = "Canonical-Ubuntu-22.04-Minimal-2023.07.19-0"
IMAGE_ID =  "ocid1.image.oc1.iad.aaaaaaaa6blpytk5nu622uj7trevp7kjxihx4byt4q6botynbyjpknk7zwna"
CIDR_BLOCK = "10.0.0.0/24"


def create_vcn(virtual_network_composite_operations, compartment_id, cidr_block):
    vcn_name = 'my_sdk_vcn'
    create_vcn_details = oci.core.models.CreateVcnDetails(
        cidr_block=cidr_block,
        display_name=vcn_name,
        compartment_id=compartment_id
    )
    create_vcn_response = virtual_network_composite_operations.create_vcn_and_wait_for_state(
        create_vcn_details,
        wait_for_states=[oci.core.models.Vcn.LIFECYCLE_STATE_AVAILABLE]
    )
    vcn = create_vcn_response.data

    print('Created VCN: {}'.format(vcn.id))
    print('{}'.format(vcn))
    print()

    return vcn


def delete_vcn(virtual_network_composite_operations, vcn):
    virtual_network_composite_operations.delete_vcn_and_wait_for_state(
        vcn.id,
        wait_for_states=[oci.core.models.Vcn.LIFECYCLE_STATE_TERMINATED]
    )

    print('Deleted VCN: {}'.format(vcn.id))
    print()


def create_subnet(virtual_network_composite_operations, vcn, availability_domain_name):
    subnet_name = 'my_sdk_subnet'
    create_subnet_details = oci.core.models.CreateSubnetDetails(
        compartment_id=vcn.compartment_id,
        availability_domain=availability_domain_name,
        display_name=subnet_name,
        vcn_id=vcn.id,
        cidr_block=vcn.cidr_block
    )
    create_subnet_response = virtual_network_composite_operations.create_subnet_and_wait_for_state(
        create_subnet_details,
        wait_for_states=[oci.core.models.Subnet.LIFECYCLE_STATE_AVAILABLE]
    )
    subnet = create_subnet_response.data

    print('Created Subnet: {}'.format(subnet.id))
    print('{}'.format(subnet))
    print()

    return subnet


def delete_subnet(virtual_network_composite_operations, subnet):
    virtual_network_composite_operations.delete_subnet_and_wait_for_state(
        subnet.id,
        wait_for_states=[oci.core.models.Subnet.LIFECYCLE_STATE_TERMINATED]
    )

    print('Deleted Subnet: {}'.format(subnet.id))
    print()



def get_launch_instance_details(compartment_id, availability_domain_name, shape_name, image_id_name, subnet, ssh_public_key):

    # We can use instance metadata to specify the SSH keys to be included in the
    # ~/.ssh/authorized_keys file for the default user on the instance via the special "ssh_authorized_keys" key.

    instance_metadata = {
        'ssh_authorized_keys': ssh_public_key,
        'some_metadata_item': 'some_item_value'
    }
 
    instance_name = 'my_sdk_instance'
    instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
        image_id=image_id_name
    )
    create_vnic_details = oci.core.models.CreateVnicDetails(
        subnet_id=subnet.id
    )
    launch_instance_details = oci.core.models.LaunchInstanceDetails(
        display_name=instance_name,
        compartment_id=compartment_id,
        availability_domain=availability_domain_name,
        shape=shape_name,
        metadata=instance_metadata,
        source_details=instance_source_via_image_details,
        create_vnic_details=create_vnic_details
    )
    return launch_instance_details


def launch_instance(compute_client_composite_operations, launch_instance_details):
    launch_instance_response = compute_client_composite_operations.launch_instance_and_wait_for_state(
        launch_instance_details,
        wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_RUNNING]
    )
    instance = launch_instance_response.data

    print('Launched Instance: {}'.format(instance.id))
    print('{}'.format(instance))
    print()

    return instance



def terminate_instance(compute_client_composite_operations, instance):
    print('Terminating Instance: {}'.format(instance.id))
    compute_client_composite_operations.terminate_instance_and_wait_for_state(
        instance.id,
        wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_TERMINATED]
    )

    print('Terminated Instance: {}'.format(instance.id))
    print()


def print_instance_details(compute_client, virtual_network_client, instance):
    # We can find the private and public IP address of the instance by getting information on its VNIC(s). This
    # relationship is indirect, via the VnicAttachments of an instance

    list_vnic_attachments_response = oci.pagination.list_call_get_all_results(
        compute_client.list_vnic_attachments,
        compartment_id,
        instance_id=instance.id
    )
    vnic_attachments = list_vnic_attachments_response.data

    vnic_attachment = vnic_attachments[0]
    get_vnic_response = virtual_network_client.get_vnic(vnic_attachment.vnic_id)
    vnic = get_vnic_response.data

    print('Virtual Network Interface Card')
    print('==============================')
    print('{}'.format(vnic))
    print()


def check_limits(limits_client, compartment_id):
    # Check Objectstorage limits 
    list_limit_values_response = limits_client.list_limit_values(
        compartment_id=compartment_id,
        service_name="object-storage",
    )
    os_limits = list_limit_values_response.data

    print('Object Storage Limits free-tier')
    print('==============================')
    print('{}'.format(os_limits))
    print()




if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError('Required: The path to the public SSH key! '
                           '  e.g. launch_oci.py ~/.ssh/my.pub' )

    with open(os.path.expandvars(os.path.expanduser(sys.argv[1])), mode='r') as file:
        ssh_public_key = file.read()

    availability_domain_name = AVAILABILTY_DOMAIN
    shape_name = SHAPE
    image_id_name = IMAGE_ID
    cidr_block = CIDR_BLOCK

    # Default config file and profile
    config = oci.config.from_file()
    compartment_id = config['tenancy']
    compute_client = oci.core.ComputeClient(config)
    compute_client_composite_operations = oci.core.ComputeClientCompositeOperations(compute_client)
    virtual_network_client = oci.core.VirtualNetworkClient(config)
    virtual_network_composite_operations = oci.core.VirtualNetworkClientCompositeOperations(virtual_network_client)
    # Initialize service client with default config file
    limits_client = oci.limits.LimitsClient(config)

    vcn = None
    subnet = None
    instance = None

    try:
        vcn = create_vcn(virtual_network_composite_operations, compartment_id, cidr_block)
        subnet = create_subnet(virtual_network_composite_operations, vcn, availability_domain_name)

        print('Launching Instance ...')
        launch_instance_details = get_launch_instance_details(
            compartment_id, availability_domain_name, shape_name, image_id_name, subnet, ssh_public_key
        )
        instance = launch_instance(compute_client_composite_operations, launch_instance_details)
        print_instance_details(compute_client, virtual_network_client, instance)
        
        # Get Objectstorage limits 
        check_limits(limits_client, compartment_id)
      

    finally:       
        import time
        print("......Sleeping for 60 seconds before destroying ..... ")
        sys.stdout.flush()
        time.sleep(60)

        if instance:
            terminate_instance(compute_client_composite_operations, instance)
        if subnet:
            delete_subnet(virtual_network_composite_operations, subnet)
        if vcn:
            delete_vcn(virtual_network_composite_operations, vcn)

    print("-- Done. Script execution completed ....")
        