<p align="center">
  <a href="https://github.com/getspine/spinesible">
    <img src="https://spi.ne/static/spinesible.png" alt="Spinesible Logo" width="256" height="253">
  </a>
</p>

Spinesible: An Ansible Backbone
===============================

[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/getspine/spinesible/blob/master/LICENSE)
[![Twitter Follow](https://img.shields.io/twitter/follow/get_spine.svg?style=social&label=Follow)](https://twitter.com/get_spine)
[![Slack](https://support.spi.ne/badge.svg)](https://support.spi.ne/)

All of [Spine's](https://spi.ne) cloud native infrastructure is automated via [Ansible](https://www.ansible.com), allowing us to swiftly perform infrastructure updates on the fly. We wrote a whole bunch of Ansible roles and scaffolding in the process and we've decided to open source it here, as we figured it'd be useful to others.

If you're just getting started with AWS and Ansible, it's our hope that this repo can give you a good starting place to work from when building an infrastructure.

Table of Contents
-----------------

   * [What is a Datacenter?](#what-is-a-datacenter)
      * [The DC Config](#the-dc-config)
      * [Step 1: Network Setup](#step-1-network-setup)
         * [Sidebar: Using DC vars](#sidebar-using-dc-vars)
      * [Step 2: Routing](#step-2-routing)
      * [Step 3: DNS](#step-3-dns)
         * [Sidebar: DC vars strike again](#sidebar-dc-vars-strike-again)
      * [Step 4: IAM](#step-4-iam)
      * [Step 5: EC2 Instances](#step-5-ec2-instances)
         * [Sections](#sections)
         * [Roles](#roles)
      * [Step 6: Configure provisioned EC2 instances](#step-6-configure-provisioned-ec2-instances)
      * [Step 7: Enjoy!](#step-7-enjoy)
   * [Further Reference](#further-reference)
      * [EC2 Dynamic Inventory](#ec2-dynamic-inventory)
      * [Repo Layout](#repo-layout)
      * [Bootstrapping](#bootstrapping)
      * [Wrappers](#wrappers)
         * [a](#a)
         * [hostvars](#hostvars)
         * [runcmd](#runcmd)
         * [ssh_push](#ssh_push)
         * [tag](#tag)
         * [tagdel](#tagdel)
         * [v](#v)
         * [vplay](#vplay)
      * [Provisioning](#provisioning)
      * [Illegal Arguments](#illegal-arguments)
      * [Custom Plugins](#custom-plugins)
   * [The Without Whom Department](#the-without-whom-department)
   * [Need Help?](#need-help)

Getting Started
---------------

1. Install Python 2.7 and virtualenv to support running Ansible:

```bash
# OS X
$ sudo easy_install-2.7 pip
$ sudo pip install virtualenv

# Ubuntu/Debian
$ sudo apt-get update
$ sudo apt-get -y install python-pip
$ sudo pip install virtualenv

# Fedora
$ sudo dnf install -y python-virtualenv

# Newer-school Red Hat (EL7+)
$ sudo yum install -y python-virtualenv

# Old-school Red Hat (older than EL7)
$ sudo yum install -y centos-release-SCL
$ sudo yum install -y python27 python27-virtualenv
$ scl enable python27
```

2. Run the environment setup script to install Ansible, the AWS CLI, and all dependencies:

```bash
$ ./setup_ansible
$ source env/bin/activate
```

By sourcing the virtualenv activation script, we add all needed binaries to the ```PATH```.

3. Create a [new administrator user in IAM](http://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started_create-admin-group.html) with **programmatic access** then create a Boto credentials file in ```~/.aws/credentials```:

```bash
cat <<EOF > ~/.aws/credentials
[us-east-1]
aws_access_key_id = <your AWS access key ID>
aws_secret_access_key = <your AWS secret access key>
EOF
```

4. Accept the terms for the CentOS 7 HVM image in the [AWS Marketplace](https://aws.amazon.com/marketplace/):

https://aws.amazon.com/marketplace/pp/B00O7WM7QW

5. Provision up the example datacenter, **us-east-1**:

```
$ ./provision_dc us-east-1
$ ssh ansibler@<a new EC2 instance IP>
```

**PLEASE NOTE**: This command will build out a lot of infrastructure, including [Aurora](http://aurora.apache.org/), [Mesos](http://mesos.apache.org/), and [Kafka](http://kafka.apache.org/), so you may wish to modify the example configuration to suit your organization's needs.

To do so, read on:

What is a Datacenter?
=====================

A datacenter is a collection of **region-based AWS resources**: VPCs, VPC subnets, security groups, internal Route 53 DNS zones, and the configured EC2 instances which will run your own services.

The DC Config
-------------

EC2 instances require an **initial AWS environment** within which to run. This step is somewhat involved, which is why many opt for the defaults offered upon the creation of an AWS account. If not using defaults, VPC creation is often performed manually via the AWS UI, which can introduce uncertainty and operator error into a complex equation.

That's why Spinesible condenses this information into a **single configuration file**, allowing you to refer to the layout of your AWS resources at a glance.

We've included an example configuration, located at ```dc_config/us-east-1.yml```. This file contains the layout for a datacenter in AWS region **us-east-1**.

To understand how best to configure your own datacenter, let's take you through the datacenter provisioning process:

Step 1: Network Setup
---------------------

First things first, we need to wire up a proper network:

```yaml
spine_vpcs_order:
  - 10.0.0.0/16

spine_vpcs:
  10.0.0.0/16:
    cidr_block: 10.0.0.0/16
    name: vpc-backbone
    tags:
      Name: vpc-backbone
    subnets:
      - cidr: 10.0.0.0/18
        az: us-east-1a
        tags:
          Name: subnet-backbone-a
      - cidr: 10.0.64.0/18
        az: us-east-1b
        tags:
          Name: subnet-backbone-b
      - cidr: 10.0.128.0/18
        az: us-east-1d
        tags:
          Name: subnet-backbone-d
      - cidr: 10.0.192.0/18
        az: us-east-1e
        tags:
          Name: subnet-backbone-e
    internet_gateway: yes
```

In our example case, we create a VPC called ```vpc-backbone``` at ```10.0.0.0/16``` then divide it up between four ```/18``` subnets, each targeted to an AWS [availability zone](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html):

**VPC 10.0.0.0/16**

| Subnet | Availability Zone |
|--------|-------------------|
| 10.0.0.0/18 | us-east-1a |
| 10.0.64.0/18 | us-east-1b |
| 10.0.128.0/18 | us-east-1d |
| 10.0.192.0/18 | us-east-1e |

Finally, we attach an [Internet gateway](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Internet_Gateway.html) to allow for connections to the outside internet.

### Sidebar: Using DC vars

After each provisioning step, pertinent information about your new resources will be recorded into ```dc_vars/us-east-1.yml```. Be certain to commit it to your Git repo after a provisioning step, as it contains valuable information that Spinesible later takes advantage of.

Step 2: Routing
---------------

Now that we've created a network, we need to configure how everything on it talks. We can do so using [VPC route tables](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Route_Tables.html):

```yaml
spine_vpc_route_tables:
  10.0.0.0/16:
    subnets:
      - 10.0.0.0/18
      - 10.0.64.0/18
      - 10.0.128.0/18
      - 10.0.192.0/18
    routes:
      - dest: 0.0.0.0/0
        gateway_id: igw
```

In our example case, any subnet within the ```10.0.0.0/16``` VPC can communicate and route out to the Internet.

To learn more about how to configure this module, refer to the [ec2_vpc_route_table module documentation](http://docs.ansible.com/ansible/ec2_vpc_route_table_module.html).

Step 3: DNS
-----------

Hostnames are a powerful concept, with the power to quickly convey useful information about any node in your infrastructure. This is why Spinesible creates custom [internal Route 53 zones](http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html):

```yaml
spine_route53_zones:
  - zone: 0.10.in-addr.arpa.
    associate_vpcs: yes
    vpcs:
      - "{{ spine_vpc_to_id['10.0.0.0/16'] }}"

  - zone: backbone.example.com.
    associate_vpcs: yes
    vpcs:
      - "{{ spine_vpc_to_id['10.0.0.0/16'] }}"
```

In this case, we create a zone called ```backbone.example.com.```, associated to the VPC we just created.

Spinesible's EC2 instance provisioner will create both forward and reverse DNS lookup records within a specified domain for each instance it creates.

This is why we need to add a reverse DNS zone for IP addresses in our VPC, those starting with ``10.0``. IP octets are inverted when performing a reverse DNS lookup:

```
lookup 10.0.34.129 -> DNS queried at 129.34.0.10.in-addr.arpa.
```

This is why we create a zone called ```0.10.in-addr.arpa.```; it will contain the reverse DNS records for all hosts provisioned in our VPC.

### Sidebar: DC vars strike again

As you might have surmised, ```spine_vpc_to_id``` is a field provided to us by our **DC vars**; in this case, it allows us to refer to the AWS VPC identifier (e.g. vpc-01268776) by CIDR identifier (e.g. 10.0.0.0/16).

Step 4: IAM
-----------

If you're like us, your application probably uses AWS services such as [S3](https://aws.amazon.com/s3/) or [DynamoDB](https://aws.amazon.com/dynamodb/). You may currently distribute the credentials needed to access these services via a configuration system, which introduces complex security considerations.

Thankfully, AWS has a useful feature called an [IAM instance profile](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html) which will dynamically inject the AWS credentials associated with an [IAM role](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html) via the [instance metadata endpoint](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html), located at the following URL on any EC2 instance:

```
http://169.254.169.254/latest/meta-data/
```

An IAM instance profile is created for every IAM role you define. In our automation, we create a role called ```spine_es``` and associate it with a policy called ```es.json.j2```, located in ```roles/provision_iam/templates/es.json.j2```:

```yaml
spine_iam_policies:
  es: es.json.j2

spine_iam_roles:
  - name: spine_es
    trust_policy: role_policy_ec2.json.j2
    policies:
      - es
```

In this case, we're configuring a role for our future [Elasticsearch](https://www.elastic.co/) nodes, with access to an S3 bucket for backups as well as permissions to describe instances for the purpose of service discovery.

```json
{
  "Statement": [
    {
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:ListBucketMultipartUploads",
        "s3:ListBucketVersions"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::{{ spine_s3_buckets.es }}"
      ]
    },
    {
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::{{ spine_s3_buckets.es }}/*"
      ]
    },
    {
      "Action": [
        "ec2:DescribeInstances"
      ],
      "Effect": "Allow",
      "Resource": [
        "*"
      ]
    }
  ],
  "Version": "2012-10-17"
}
```

Step 5: EC2 Instances
---------------------

Now that we've handled all that, we're ready to provision our EC2 instances.

### Sections

EC2 instances are provisioned into something called a **section**, which is associated to **one or more VPCs** and **a single internal Route 53 zone**. Let's have a look at our example section, ```backbone```: 

```yaml
spine_sections:
  backbone:
    route53_zone: backbone.example.com

    vpcs:
      - 10.0.0.0/16

    default_egress_rules:
      - proto: all
        from_port: 0
        to_port: 65535
        cidr_ip: 0.0.0.0/0

    provisioning_order:
      - bastion
      - aurora
      - aggregator
      - compute

    roles:
      aggregator:
        image: "{{ spine_base_ami }}"
        base_volume_snapshot: "{{ spine_base_snapshot }}"
        instance_type: m3.medium
        instance_profile_name: spine_es
        quantity: 3
        base_volume_type: gp2
        base_volume_size_gb: 100
        sg_rules:
          - proto: tcp
            from_port: 22
            to_port: 22
            cidr_ip: 0.0.0.0/0
          - proto: tcp
            from_port: 5140
            to_port: 5140
            cidr_ip: 10.0.0.0/16
```

All nodes provisioned in the ```backbone``` section will land in our VPC, ```10.0.0.0/16```, and will have a DNS record created in the ```backbone.example.com``` Route 53 zone. Each DNS record will be in the following form:

```
<role name>-<node id>.<Route 53 zone>

e.g:
aggregator-40b3a474.backbone.example.com
```

### Roles

Roles map EC2 instances to Ansible automation; you'll see that for each specified under the ```roles``` section (aggregator), there is a corresponding playbook in the root of this repo (aggregator.yml). You can specify a comprehensive range of useful machine configuration here, including [EBS volume size](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSVolumes.html) and type and [security group rules](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html).

With this information, Spinesible's provisioning automation will proceed to create EC2 instances, spread across Amazon availability zones, within the constraints you've specified. Each of these will be stamped with several useful [tags](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Tags.html) along the way:

```
Name: <role name>-<node id>
ansible_group: <role name>
hostname: <role name>-<node id>.<Route 53 zone>
needs_bootstrap: True
spine_section: <section name>

e.g:
Name: aggregator-40b3a474
ansible_group: aggregator
hostname: aggregator-40b3a474.backbone.example.com
needs_bootstrap: True
spine_section: backbone
```

Spinesible is fairly liberal in its creation of tags as they can be used to target Ansible automation in tandem with the included EC2 dynamic inventory script.

Step 6: Configure provisioned EC2 instances
-------------------------------------------

Provisioning is complete, pat yourself on the back!

Next up, we need to take our raw CentOS 7 images and apply our base configuration, which includes organizational SSH keys, SELinux settings, and package installation/updates. The application of this common configuration is known as the **bootstrapping process**.

Nodes undergoing bootstrapping are targeted by way of the following tag value: ```needs_bootstrap: True```. After each node is sufficiently bootstrapped, this tag will be changed to ```needs_bootstrap: False```.

After bootstrapping completes, we can begin configuring our services. To do so, we simply run each base role Playbook in the order specified by the ```provisioning_order``` given above.

This particular task is accomplished by way of a utility script, ```utils/setup_spine_dc_sections```.

Step 7: Enjoy!
--------------

These tasks complete, you should have a battle-tested set of cloud native services at your beck and call. To log into any EC2 instance, simply SSH as the ```ansibler``` user.

Further Reference
=================

The sections below provide additional documentation for the components of the Spinesible framework:

EC2 Dynamic Inventory
---------------------

The EC2 dynamic inventory script can generate a large number of Ansible [host groups](http://docs.ansible.com/ansible/intro_inventory.html#hosts-and-groups) against which automation can be targeted. To see which host groups you can target against, simply run the script directly:

```bash
$ ./inventory/ec2
{
  ...
  "tag_hostname_bastion_40b3a474_backbone_example_com": [
    "34.206.71.36"
  ],
  "tag_needs_bootstrap_False": [
    "34.206.71.36"
  ],
  "tag_spine_section_backbone": [
    "34.206.71.36"
  ],
  "type_t2_small": [
    "34.206.71.36"
  ],
  "us-east-1": [
    "34.206.71.36"
  ],
  "us-east-1a": [
    "34.206.71.36"
  ],
  "vpc_id_vpc_24393442": [
    "34.206.71.36"
  ]
}
```

The creation of the initial inventory can take a while, so the inventory script will cache the results.

To speed up Ansible operations, we've set an arbitrarily high cache timeout (1 hour), but this can be overridden by setting the following environment variable:

```bash
export PURGE_EC2_CACHE=true
```

Repo Layout
-----------

This repo makes heavy use of [Ansible roles](http://docs.ansible.com/ansible/playbooks_roles.html) to allow for easy composition of infrastructure automation.  These can be found in the ```roles``` subdirectory.

Playbooks for each server class can be found in the base of this repo. If you're familiar with Puppet or Chef, these Ansible playbooks work very much like [Puppet nodeclasses](https://docs.puppet.com/puppet/4.9/lang_node_definitions.html) or [Chef cookbooks](https://docs.chef.io/cookbooks.html), composing together roles and service configuration.

For instance, this playbook establishes Elasticsearch data nodes across all servers in the **tag_ansible_group_es_data** group:

```yaml
---
- name: Establishes and maintains an Elasticsearch datanode
  hosts: tag_ansible_group_es_data
  become: yes
  become_user: root
  become_method: sudo

  vars_files:
    - "dc_config/{{ lookup('env', 'SPINE_DATACENTER') }}.yml"
    - "dc_vars/{{ lookup('env', 'SPINE_DATACENTER') }}.yml"

  vars:
    elasticsearch_cluster_name: "spinesible-{{ spine_datacenter }}"
    elasticsearch_discovery_zen_minimum_master_nodes: 1
    elasticsearch_discovery_zen_ping_multicast_enabled: no
    elasticsearch_memory_bootstrap_mlockall: yes
    elasticsearch_node_data: yes
    elasticsearch_node_master: no
    elasticsearch_plugin_aws_region: "{{ spine_datacenter }}"
    elasticsearch_plugin_aws_tag_filters:
      es_cluster: "spinesible-{{ spine_datacenter }}"
    elasticsearch_should_format_volumes: yes
    elasticsearch_total_ram_pct: 50.0

  roles:
    - elasticsearch
```

The **tag_ansible_group_es_data** group maps to those produced by the EC2 dynamic inventory.

This structure makes it easy to add new services to nodes. Simply add a new role to the ```roles``` list then add overrides to the ```vars``` section to configure it.

Bootstrapping
-------------

```bash
./bootstrap [datacenter] [ansible_hosts_tag]
```

The **bootstrap** role contains a **base configuration that all nodes utilize** and **ensures that the base configuration is up-to-date**.

To update **all nodes in a datacenter**:

```bash
./bootstrap us-east-1 all

PLAY [Bootstrap new server node] ***********************************************

TASK [setup] *******************************************************************
ok: [107.22.135.212]

TASK [epel : Bootstrap ansible-bootstrap-epel Yum repository] ******************
ok: [107.22.135.212]
...
```

To update a **single nodeclass**:

```bash
./bootstrap us-east-1 tag_ansible_group_aurora

PLAY [Bootstrap new server node] ***********************************************

TASK [setup] *******************************************************************
ok: [107.22.135.212]

TASK [epel : Bootstrap ansible-bootstrap-epel Yum repository] ******************
ok: [107.22.135.212]
...
```

Wrappers
--------

In the interest of simplicity, we've included a few wrapper scripts to simplify the invocation of Ansible. They tie in our EC2 dynamic inventory, virtualenv Ansible binaries, and aforementioned datacenter configuration system.

### a

```bash
./a [datacenter] [args]
```

Works like calling the 'ansible' binary directly; arguments are simply passed through.  For instance, you could obtain the full list of Ansible host facts like so:

```bash
./a us-east-1 tag_ansible_group_aurora -m setup

107.22.135.212 | SUCCESS => {
    "ansible_facts": {
        "ansible_all_ipv4_addresses": [
            "10.0.32.18"
        ],
        "ansible_all_ipv6_addresses": [
            "fe80::c00:23ff:fea1:60f8"
        ],
        "ansible_architecture": "x86_64",
        "ansible_bios_date": "12/09/2016",msg": "Hello world!"
    ...
}
```

### hostvars

```bash
./hostvars [datacenter] [ansible_hosts_tag]
```

Dumps the Ansible hostvars for all hosts matching the provided tag, such as ```tag_ansible_group_aurora``` or ```tag_ansible_group_es_master```:

```bash
./hostvars us-east-1 tag_ansible_group_aaa

107.22.135.212 | SUCCESS => {
    "hostvars": {
        "107.22.135.212": {
            "ansible_check_mode": false,
            "ansible_version": {
                "full": "2.2.1.0",
                "major": 2,
                "minor": 2,
                "revision": 1,
                "string": "2.2.1.0"
            },
    ...
```

### runcmd

```bash
./runcmd [datacenter] [ansible_group] '[command]'
```

Convenience wrapper for a **root Bash command blast** across all nodes in the provided ```ansible_group```, like ```aurora``` or ```jenkins```.  Be certain that all **commands are enclosed within single-quotes** like above.

```bash
./runcmd us-east-1 aaa 'whoami'

 - Executing shell command across group aaa in us-east-1: whoami
107.22.135.212 | SUCCESS | rc=0 >>
root
```

### ssh_push

```bash
./ssh_push [datacenter] [ansible_hosts_tag]
```

Distributes all SSH keys (from the bootstrap role) to all the nodes matching the provided Ansible hosts tag.

```bash
./ssh_push us-east-1 tag_ansible_group_aaa

PLAY [Bootstrap new server node] ***********************************************

TASK [setup] *******************************************************************
ok: [107.22.135.212]

TASK [selinux : Apply all SELinux modules] *************************************

TASK [bootstrap : Add initial user's authorized keys] **************************
ok: [107.22.135.212] =>
...
```

### tag

```bash
./tag [datacenter] [ansible_group] [key] [value]
```

Adds an EC2 tag to the provided Ansible group.

### tagdel

```bash
./tagdel [datacenter] [ansible_group] [key] [value]
```

Removes an EC2 tag from the provided Ansible group.

### v

```bash
./v [datacenter] [args]
```

Works like calling the 'ansible-playbook' binary directly, including **Vault parameters** authenticated by ```--vault-password-file ~/.vault```.

```bash
./v us-east-1 aaa.yml

PLAY [Establishes a AAA (Authentication, Authorization, and Accounting) node] ***

TASK [setup] *******************************************************************
ok: [107.22.135.212]

TASK [awscli : Ensure that the AWS CLI is installed] ***************************
ok: [107.22.135.212]
```

### vplay

```bash
./vplay [datacenter] [args]
```

Works like calling the 'ansible-playbook' binary directly, including **Vault parameters** authenticated by **direct console password input**.

```bash
./v us-east-1 aaa.yml
Vault password:

PLAY [Establishes a AAA (Authentication, Authorization, and Accounting) node] ***

TASK [setup] *******************************************************************
ok: [107.22.135.212]

TASK [awscli : Ensure that the AWS CLI is installed] ***************************
ok: [107.22.135.212]
```

Using the Vault
---------------

Wrapper scrips such as ```v``` and ```vplay``` take advantage of the [Ansible Vault](http://docs.ansible.com/ansible/playbooks_vault.html), a feature which encrypts sensitive credentials, allowing them to be checked into a source repo like this one.

We've provided an example vault configuration in ```vault/creds.yml```, locked with the following password:

```please change this password```

As it suggests, you should change this password immediately. To do so:

```bash
$ source env/bin/activate
$ ansible-vault rekey vault/creds.yml
Vault password:
New Vault password:
```

If multiple members of your team edit the Vault file simultaneously, you can use the script located in ```vault/vault-merge.sh``` to merge all encrypted contents.

Provisioning
------------

Spinesible's provisioning automation will provision all necessary resources to run complex services within a datacenter.  All datacenters **need to be configured** with a file in the ```dc_config``` subdir; furthermore, **any resources they create** will be tracked via a **dynamically-updated file** in the ```dc_vars``` subdir.

The provisioning process is divided into **four phases**:

**Provision**

Establishes VPCs, VPC subnets, IAM settings, Route53 zones, S3 buckets, and, finally, all needed EC2 instances.  All fresh EC2 instances are tagged with ```needs_bootstrap: True```, which is used to target the next phase, **Bootstrap**.

**Bootstrap**

Establishes a base environment on the freshly-provisioned nodes; once this step is accomplished, sets ```needs_bootstrap: False```.

**Setup**

Runs nodeclass automation files (e.g. aaa.yml, aurora.yml, etc), ordered by spine_section and the provisioning_order settings.

This automation is designed to be idempotent, so feel free to run it as many times as you'd like.

Illegal Arguments
-----------------

Please note: users **should not directly set** the ```-i``` or ```-u``` variables as they are **pre-configured by all scripts**.

Custom Plugins
--------------

Ansible allows us to **dynamically extend its functionality** via **custom Python plugins**.  We primarily make use of **filter plugins** to help us coerce Ansible hostvars data into the forms that certain server applications expect (such as ordered Zookeeper hosts and myids).

These plugins can be found under the ```plugin``` subdir, and developer documentation can be found here:

http://docs.ansible.com/ansible/dev_guide/developing_plugins.html

The Without Whom Department
===========================

This repository makes use of some excellent open source roles from the [Ansible Galaxy](https://galaxy.ansible.com/) community:

[Jeff Geerling](https://www.jeffgeerling.com/)

 - ```geerlingguy.ntp```: https://github.com/geerlingguy/ansible-role-ntp
 - ```geerlingguy.logstash```: https://github.com/geerlingguy/ansible-role-logstash

[Kyle Lexmond](https://kyle.io/)

 - ```kyl191.openvpn```: https://github.com/kyl191/ansible-role-openvpn

[Jeff Widman](http://www.jeffwidman.com/blog/)

 - ```jeffwidman.yum-cron```: https://github.com/jeffwidman/ansible-yum-cron

To install new roles from the Galaxy, simply use the ansible-galaxy command:

```bash
$ source env/bin/activate
$ ansible-galaxy install your.role
```

Need Help?
==========

If you run into any issues, feel free to [file a Github issue](https://github.com/getspine/spinesible/issues/new) or [join our Slack](https://support.spi.ne). We'd be glad to help you get things working.

From all of us here at [Spine](https://spi.ne), we hope that this automation helps you build some cool things!

<p align="center">
  <a href="https://spi.ne">
    <img src="https://spi.ne/static/logo_small.png" alt="Spine Logo" width="100" height="98">
  </a>
</p>
