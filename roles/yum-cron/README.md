yum-cron
=========

Installs and manages `yum-cron`.

By default this role installs security updates every hour, and checks for but
does not install normal updates daily. For updates that aren't security flaws, I
prefer to delay upgrading until I'm available to fix anything that might go wrong.

Since the daily update level only checks but doesn't download, the notification
message will say "empty transaction", meaning it found an update, but didn't do
anything about it.

Requirements
------------

Tested on CentOS 7.
Will likely work on equivalent RHEL or RHEL derivatives.

Role Variables
--------------

You'll likely want to change the default `email_to` variable to an email address
that you actually monitor.

It's also possible to define special yum settings to for example exclude some packages from auto-updating:

<pre>
#hourly_base_options:
# - "exclude=java*,kernel*"

#daily_base_options: "{{ hourly_base_options }}"
</pre>

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: yum-cron, email_to: support@rockclimbing.com, tags: ['yum_cron'] }

License
-------

MIT

Author Information
------------------

Jeff Widman jeff@jeffwidman.com
Johan Guldmyr jguldmyr@csc.fi
