"""
Configuration Generator for LLMServingSim Network and Memory Settings

This module generates network topology and memory configuration files for ASTRA-Sim.

Supported Network Topologies:
    The ASTRA-Sim network backend supports the following topology building blocks:
    - Ring: Ring topology connecting NPUs in a circular fashion
    - FullyConnected: Fully connected topology where each NPU connects to all others
    - Switch: Switch-based topology for NPU interconnection
    
    Note: The current implementation uses 'FullyConnected' topology by default.
    To use other topologies, modify the topology value in create_network_config().
"""

import json
import yaml
import math

class FlowStyleList(list): pass

def represent_flowstyle_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.add_representer(FlowStyleList, represent_flowstyle_list)

def create_network_config(astra_sim, npu_nums, npu_group, link_bw, link_latency):
    """
    Generates network topology configuration for ASTRA-Sim.
    
    This function creates a multi-dimensional network configuration YAML file
    based on the number of NPUs and their grouping for parallelism.
    
    Args:
        astra_sim (str): Path to the ASTRA-Sim directory
        npu_nums (int): Total number of NPUs
        npu_group (int): NPU group size for controlling parallelism
                        (npu_group == 1: tensor parallelism, 
                         npu_nums == npu_group: pipeline parallelism)
        link_bw (float): Bandwidth of the network link in GB/s
        link_latency (float): Latency of the network link in nanoseconds
    
    Returns:
        str: Path to the generated network configuration file
        
    Topology Support:
        Currently uses 'FullyConnected' topology for all network dimensions.
        Other supported topologies in ASTRA-Sim include:
        - 'Ring': For ring-based interconnection
        - 'Switch': For switch-based interconnection
        
        To use a different topology, modify the topology field in topology_data.
        Example: FlowStyleList(["Ring"] * network_dim)
    """
    
    network_dim = int(math.log2(npu_group))+1
    if npu_nums == npu_group:
        # full pipeline parallelism, one dimension is sufficient
        network_dim = 1
    output_file = astra_sim+f'/inputs/network/network.yml'
    npus_per_dim = npu_nums//(2**(network_dim-1)) 

    # Supported topologies: "Ring", "FullyConnected", "Switch"
    # Current default: "FullyConnected"
    topology_data = {
        "topology": FlowStyleList(["FullyConnected"] * network_dim),
        "npus_count": FlowStyleList([npus_per_dim if i == 0 else 2 for i in range(network_dim)]),
        "bandwidth": FlowStyleList([float(link_bw)] * network_dim),
        "latency": FlowStyleList([float(link_latency)] * network_dim)
    }

    with open(output_file, 'w') as yaml_file:
        yaml.dump(topology_data, yaml_file, default_flow_style=False, sort_keys=False)

    return output_file

def set_remote_bandwidth(remote, remote_bw):
    """
    Modify the remote (host) memory bandwidth configuration.
    
    Args:
        remote (str): Path to the remote memory configuration JSON file
        remote_bw (float): Remote memory bandwidth in GB/s
    
    Returns:
        str: Path to the modified remote memory configuration file
    """
    with open(remote, 'r') as json_file:
        data = json.load(json_file)

    if "remote-mem-latency" in data and "remote-mem-bw" in data:
        data["remote-mem-latency"] = 0              # Modify if needed
        data["remote-mem-bw"] = remote_bw

    with open(remote, 'w') as json_file:
        json.dump(data, json_file, indent=2)

    return remote
    