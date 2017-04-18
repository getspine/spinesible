#!/bin/bash

kdb5_ldap_util -D cn=admin,dc=c,dc=spi,dc=ne -H ldap://aaa.c.spi.ne create -subtrees "ou=krb5,dc=c,dc=spi,dc=ne" -r C.SPI.NE -s && touch /var/kerberos/ldap_synced

kdb5_ldap_util -D cn=admin,dc=c,dc=spi,dc=ne stashsrvpw -f /var/kerberos/krb5kdc/C.SPI.NE.ldap_service_pw cn=kdc,ou=krb5,dc=c,dc=spi,dc=ne
kdb5_ldap_util -D cn=admin,dc=c,dc=spi,dc=ne stashsrvpw -f /var/kerberos/krb5kdc/C.SPI.NE.ldap_service_pw cn=kadmin,ou=krb5,dc=c,dc=spi,dc=ne
