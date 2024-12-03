#!/usr/bin/env python3
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
import json
import sys

def get_vmss_instances(resource_group, vmss_name):
    credential = DefaultAzureCredential()
    compute_client = ComputeManagementClient(credential, os.environ['AZURE_SUBSCRIPTION_ID'])
    network_client = NetworkManagementClient(credential, os.environ['AZURE_SUBSCRIPTION_ID'])

    # Get VMSS instances
    vmss_vms = compute_client.virtual_machine_scale_set_vms.list(resource_group, vmss_name)

    inventory = {
        '_meta': {'hostvars': {}},
        'aks_nodes': {'hosts': [], 'vars': {}}
    }

    for vm in vmss_vms:
        # Get network interface details
        nic_reference = vm.network_profile.network_interfaces[0]
        nic_name = nic_reference.id.split('/')[-1]
        nic = network_client.network_interfaces.get(resource_group, nic_name)

        # Get private IP
        private_ip = nic.ip_configurations[0].private_ip_address

        # Add to inventory
        inventory['aks_nodes']['hosts'].append(private_ip)
        inventory['_meta']['hostvars'][private_ip] = {
            'ansible_host': private_ip,
            'vmss_name': vmss_name,
            'resource_group': resource_group
        }

    return inventory

def main():
    # This would be called by Ansible with specific arguments
    print(json.dumps(get_vmss_instances(sys.argv[1], sys.argv[2])))

if __name__ == '__main__':
    main()
