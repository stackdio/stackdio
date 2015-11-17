LDAP Guide
==========

django-auth-ldap
----------------

Under the hood, we use `django-auth-ldap`_ for all our interaction with an LDAP server.
It's a very useful library that allows us to integrate with LDAP in just a few lines of
python configuration.


LDAP and stackd.io
------------------

If you'd like to integrate with LDAP, all you need to do is create an ``ldap_settings.py`` file
in the ``stackdio.server.settings`` package.  If this file exists, stackd.io will automatically
pick it up and begin authenticating users to your ldap server.  Inside that settings package,
there is an ``ldap_settings.py.template`` file that you may rename to ``ldap_settings.py``
and update to match your needs.  It's contents are displayed below.

The template contains most of the relevant bits you may want to use, but we defer anything
deeper to the `django-auth-ldap`_ documentation.


.. code:: python

    ##
    # LDAP configuration
    # We are using django-auth-ldap to enable stackd.io to use LDAP for
    # authentication. The settings below correspond to our internal
    # LDAP and we don't guarantee this to work for all. Please see
    # the docs at http://pythonhosted.org/django-auth-ldap/ for more
    # information.
    ##

    import ldap
    from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

    # We use direct binding with a dedicated user. If you have anonymous
    # access available or can bind with any user, you'll want to change
    # this.
    AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = False
    AUTH_LDAP_SERVER_URI = 'YOUR_LDAP_SERVER_URI'
    AUTH_LDAP_BIND_DN = 'uid=YOUR_BIND_USER,ou=People,dc=yourcompany,dc=com'
    AUTH_LDAP_BIND_PASSWORD = 'YOUR_BIND_USER_PASSWORD'

    AUTH_LDAP_REQUIRE_GROUP = ('cn=stackdio-user,ou=Group,dc=yourcompany,dc=com')
    AUTH_LDAP_USER_SEARCH = LDAPSearch('ou=People,dc=yourcompany,dc=com',
                                       ldap.SCOPE_SUBTREE,
                                       '(&(objectClass=Person)(uid=%(user)s))')

    # Group handling.  Read the django_auth_ldap documentation for more info.
    AUTH_LDAP_FIND_GROUP_PERMS = False
    AUTH_LDAP_MIRROR_GROUPS = False

    AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
        'ou=Group,dc=yourcompany,dc=com',
        ldap.SCOPE_SUBTREE,
        '(objectClass=groupOfNames)'
    )

    AUTH_LDAP_USER_ATTR_MAP = {
        'first_name': 'givenName',
        'last_name': 'sn',
        'email': 'mail',
    }

    AUTH_LDAP_USER_FLAGS_BY_GROUP = {
        'is_superuser': 'cn=stackdio-admin,ou=Group,dc=yourcompany,dc=com',
        'is_staff': 'cn=stackdio-admin,ou=Group,dc=yourcompany,dc=com',
    }

    AUTH_LDAP_CONNECTION_OPTIONS = {
        ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
        ldap.OPT_X_TLS_NEWCTX: 0,
    }


.. _django-auth-ldap: https://pythonhosted.org/django-auth-ldap/
