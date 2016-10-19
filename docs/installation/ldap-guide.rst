LDAP Guide
==========

django-auth-ldap
----------------

Under the hood, we use `django-auth-ldap`_ for all our interaction with an LDAP server.
It's a very useful library that allows us to integrate with LDAP in just a few lines of configuration.


LDAP and stackd.io
------------------

If you'd like to integrate with LDAP, you must install the ``ldap`` extra and add an ``ldap`` section to the ``stackdio.yaml`` file
(usually located at ``/etc/stackdio/stackdio.yaml`` or ``$HOME/.stackdio/stackdio.yaml``).

To install the ``ldap`` extra:

.. code:: bash

    pip install stackdio-server[ldap]

An example configuration is shown below.

The example contains most of the relevant bits you may want to use,
but we defer anything deeper to the `django-auth-ldap`_ documentation.

Any key / value pair that appears in the ``ldap`` section of the config file will be uppercased and appended to ``AUTH_LDAP_`` before being placed in the config file.
For example, having ``server_uri: ldaps://example.com`` in your stackdio config file will translate to the django-auth-ldap config of ``AUTH_LDAP_SERVER_URI = 'ldaps://example.com'``.

.. note::

    If you're using the packer-built AMI described in :doc:`ami`,
    your stackdio.yaml is located at ``/etc/stackdio/stackdio.yaml``.


.. code:: yaml

    ##
    # Optional LDAP configurations
    # To be appended to your stackdio.yaml file.

    ldap:
      # This must be set to true for anything below to take effect
      enabled: true

      # The url of your server (can be a comma-separated list of servers)
      server_uri: ldaps://ldap.example.com

      # Should we bind to LDAP as the user trying to login?
      bind_as_authenticating_user: false

      # if bind_as_authenticating_user is false, provide the bind user credentials
      bind_dn: 'uid=binduser,ou=People,dc=example,dc=com'
      bind_password: my_password

      # Should groups in ldap be mirrored to django groups in the database?
      mirror_groups: true

      # Deny login if a valid LDAP user isn't in this list of groups
      #require_group:
      #  - 'cn=mygroup,ou=People,dc=example,dc=com'

      # The search parameters for users.
      #   The result of a search using these parameters should return EXACTLY ONE
      #   user for this to work properly.
      user_search_base: 'ou=People,dc=example,dc=com'
      user_search_scope: SCOPE_SUBTREE
      user_search_filter: '(&(objectClass=Person)(uid=%(user)s))'

      # The search parameters for groups.
      #   The result of a search using these parameters should return an exhaustive list
      #   of groups you would like to make available.
      group_search_base: 'ou=Group,dc=eample,dc=com'
      group_search_scope: SCOPE_SUBTREE
      #group_search_filter: '(objectClass=*)'

      # The type of the ldap groups
      group_type: GroupOfNamesType

      # A map from django user object attributes to the associated attributes in LDAP
      user_attr_map:
        first_name: givenName
        last_name: sn
        email: mail

      # A map that associates boolean user flags to LDAP groups
      # i.e. if an LDAP user is in the specified LDAP group, the specified user flag is set to 'True'
      user_flags_by_group:
        is_superuser: 'cn=admin,ou=Group,dc=example,dc=com'
        is_staff: 'cn=admin,ou=Group,dc=example,dc=com'

      # Any connection options you need
      connection_options:
        OPT_X_TLS_REQUIRE_CERT: OPT_X_TLS_NEVER
        OPT_X_TLS_NEWCTX: 0


.. _django-auth-ldap: https://pythonhosted.org/django-auth-ldap/
