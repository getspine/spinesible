import os
import re
import urlparse

from copy import copy
from datetime import datetime


ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class SpineFilterError(Exception):
  pass


class NoMyidFoundError(SpineFilterError):
  pass


def grab_ssh_key(some_list):
  r = re.compile('^ssh-rsa .*$')
  ssh_keys = filter(r.match, some_list)
  if ssh_keys[0]:
    return ssh_keys[0]
  else:
    return ""


def merge_drone_sg_rules(sg_rules, drone_sg_rules, drone_vpcs):
  '''
  Merges a role's sg_rules section with a drone_sg_rules section.
  '''

  merged_rules = sg_rules
  for drone_vpc in drone_vpcs:
    for drone_sg_rule in drone_sg_rules:
      sg_rule_with_vpc = copy(drone_sg_rule)
      sg_rule_with_vpc['cidr_ip'] = drone_vpc
      merged_rules.append(sg_rule_with_vpc)
  return merged_rules


def hostvar(hostvars, inventory_host, key):
  hv = hostvars[inventory_host]
  return hv[key]


def zk_myid(hostvars, inventory_hosts, inventory_host):
  '''
  Returns the canonical ZK myid of the provided host.
  '''

  hv = hostvars[inventory_host]
  if 'ec2_tag_zk_myid' in hv:
    return int(hv['ec2_tag_zk_myid'])
  else:
    sorted_hostvars = sorted([hostvars[host] for host in inventory_hosts],
        key=lambda hv: datetime.strptime(hv['ec2_launch_time'], ISO8601_FORMAT))  
    sorted_ips = [hv['ec2_ip_address'] for hv in sorted_hostvars]
    try:
      return sorted_ips.index(inventory_host) + 1
    except ValueError:
      raise NoMyidFoundError('No myid found for host {0} in hosts: {1}'.format(
          inventory_host, inventory_hosts))


def kafka_broker_id(hostvars, inventory_hosts, inventory_host):
  '''
  Returns the canonical Kafka broker ID of the provided host.
  '''

  hv = hostvars[inventory_host]
  if 'ec2_tag_kafka_broker_id' in hv:
    return int(hv['ec2_tag_kafka_broker_id'])
  else:
    sorted_hostvars = sorted([hostvars[host] for host in inventory_hosts],
        key=lambda hv: datetime.strptime(hv['ec2_launch_time'], ISO8601_FORMAT))  
    sorted_ips = [hv['ec2_ip_address'] for hv in sorted_hostvars]
    try:
      return sorted_ips.index(inventory_host) + 1
    except ValueError:
      raise NoMyidFoundError('No myid found for host {0} in hosts: {1}'.format(
          inventory_host, inventory_hosts))


def zk_private_ips(hostvars, inventory_hosts):
  '''
  Converts a list of public host IPs to private IPs, each sorted by their EC2 instance
  creation date in the form: 2017-01-28T23:00:14.000Z.  Additionally, users can specify
  a 'zk_myid' EC2 tag with an explicit myid in node replacement cases.

  This allows us to ensure that ZooKeeper hosts are kept in a consistent order when
  expanding the size of a quorum.
  '''

  sorted_hostvars_by_launch = sorted([hostvars[host] for host in inventory_hosts],
      key=lambda hv: datetime.strptime(hv['ec2_launch_time'], ISO8601_FORMAT))
  
  sorted_ips = {}
  for i in range(len(sorted_hostvars_by_launch)):
    hv = sorted_hostvars_by_launch[i]
    if 'ec2_tag_zk_myid' in hv:
      # If a user has tagged the node with zk_myid: <n>, uses this as the index instead.
      sorted_ips[int(hv['ec2_tag_zk_myid'])] = hv['ec2_private_ip_address']
    else:
      sorted_ips[i] = hv['ec2_private_ip_address']

  return [sorted_ips[index] for index in sorted(sorted_ips.keys())]


def private_ips_with_port(hostvars, inventory_hosts, port):
  '''
  Obtains a set of private IPs and appends a :port to each item.
  '''

  sorted_hostvars_by_launch = sorted([hostvars[host] for host in inventory_hosts],
      key=lambda hv: datetime.strptime(hv['ec2_launch_time'], ISO8601_FORMAT))
  
  sorted_ips = {}
  for i in range(len(sorted_hostvars_by_launch)):
    hv = sorted_hostvars_by_launch[i]
    if 'ec2_tag_zk_myid' in hv:
      # If a user has tagged the node with zk_myid: <n>, uses this as the index instead.
      sorted_ips[int(hv['ec2_tag_zk_myid'])] = hv['ec2_private_ip_address']
    else:
      sorted_ips[i] = hv['ec2_private_ip_address']

  return [':'.join([sorted_ips[index], str(port)]) for index in sorted(sorted_ips.keys())]


def ip_to_inaddr_zone(ip_address):
  '''
  Converts an IP address to the in-addr.arpa. Route53 zone it should land in.
  '''

  return '.'.join(ip_address.strip().split('.')[::-1][2:4])


def ip_to_inaddr_record(ip_address):
  '''
  Converts an IP address to the in-addr.arpa. Route53 record it should land in.
  '''

  return '.'.join([
    '.'.join(ip_address.strip().split('.')[::-1]),
    'in-addr.arpa.',
  ])


def private_hostnames(hostvars, inventory_hosts, suffix=''):
  '''
  Converts a list of public host IPs to their private Spine hostname.
  '''

  return [''.join([hostvars[host]['ec2_tag_hostname'], suffix])
    for host in inventory_hosts]


def private_ips(hostvars, inventory_hosts, suffix=''):
  '''
  Converts a list of public host IPs to their private IPs.
  '''

  return [''.join([hostvars[host]['ec2_private_ip_address'], suffix])
    for host in inventory_hosts]


def ruby_major_version(version_number):
  '''
  Returns the major version (e.g. X.X) of a Ruby release version (e.g. X.X.Y)
  '''

  return '.'.join(version_number.split('.')[0:-1])


def url_to_path(self, url):
  parsed = urlparse.urlparse(url)
  return os.path.abspath(os.path.join(parsed.netloc, parsed.path))


def with_prefix(string_list, prefix):
  '''
  Adds a string prefix to all strings in the provided list.
  '''

  return ['{0}{1}'.format(prefix, item) for item in string_list]


class FilterModule(object):
  def filters(self):
    return {
      'grab_ssh_key': grab_ssh_key,
      'hostvar': hostvar,
      'ip_to_inaddr_record': ip_to_inaddr_record,
      'ip_to_inaddr_zone': ip_to_inaddr_zone,
      'kafka_broker_id': kafka_broker_id,
      'merge_drone_sg_rules': merge_drone_sg_rules,
      'private_hostnames': private_hostnames,
      'private_ips': private_ips,
      'private_ips_with_port': private_ips_with_port,
      'ruby_major_version': ruby_major_version,
      'url_to_path': url_to_path,
      'with_prefix': with_prefix,
      'zk_myid': zk_myid,
      'zk_private_ips': zk_private_ips,
    }
