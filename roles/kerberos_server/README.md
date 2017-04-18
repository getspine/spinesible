ansible-kerberos-server
=======================

[![Build Status](https://travis-ci.org/AlberTajuelo/ansible-kerberos-server.svg?branch=master)](https://travis-ci.org/AlberTajuelo/ansible-kerberos-server)

**ansible-kerberos-server** is an Ansible role to easily install a Kerberos Server.

This role is inspired in "bennojoy/kerberos_server" work.

Requirements
------------

In order to use this Ansible role, you will need:

* Ansible version >= 2.2 in your deployer machine.
* Check meta/main.yml if you need to check dependencies.

Installation
------------

**ansible-kerberos-server** is an Ansible role distributed globally using [Ansible Galaxy](https://galaxy.ansible.com/). In order to install **ansible-kerberos-server** role you can use the following command.

```
$ ansible-galaxy install AlberTajuelo.kerberos-server
```

Update
------

If you want to update the role, you need to pass **--force** parameter when installing. Please, check the following command:

```
$ ansible-galaxy install --force AlberTajuelo.kerberos-server
```

Main workflow
-------------

This role does:
* Download specific Kerberos packages (this packages are os-dependent).
* Configuring Kerberos Server files:
 * kdc.conf
 * kadm5.acl
 * krb5.conf
* Create an admin user

Role Variables
--------------


| Attribute 		| Default Value 	| Description  									|
|---        		|---				|---											|
| kdc_realm_name  		| REALM.NAME.COM	| Realm Name for Kerberos Server				|
| kdc_port  		| 88			  	| Kerberos Key Distribution Center (KDC) port 	|
| krb_force_recreate_database  	| no   	| force delete the current database for kdc_realm_name 					  	|
| kdc_master_db_pass  	| m4st3r_p4ssw0rd  	| Administrator password					  	|
| create_kadmin_user  	| yes   	| toggle creation of admin user 					  	|
| kadmin_user  		| defaultuser 	 	| Kadmin username							  	|
| kadmin_pass  		| d3f4ultp4ss  		| Kadmin password							  	|


Example Playbook
----------------

In the folder, `example` you can check an example project that shows how to deploy a Kerberos Server in two hosts.

In order to run it, you will need to have Vagrant and the **ansible-kerberos-server** role installed. Please check https://www.vagrantup.com for more information about Vagrant and our Installation section.

```
$ cd example/my-playbook
$ vagrant up
$ ansible-playbook -i hosts deploy.yml
```

You can check more advanced examples inside the test folder which are run against Travis-CI.

License
-------

MIT

Future Improvements
-------------------

- [ ] Possibility to create multiple KDC slaves.
- [ ] Flag to enable/disable to create an admin user.
- [ ] Disable linking "/dev/urandom" to "/dev/random" and use a "secure" random generator tool (could be "haveged"?).
- [ ] Install NTP firstly.
- [ ] Possibility to have multiple KDC ports.
- [ ] Enable/disable enctypes.
- [ ] Adding more ACLs.
- [ ] Create a list of keytabs.

Author Information
------------------

AlberTajuelo (@AlberTajuelo)
