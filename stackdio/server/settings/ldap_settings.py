import ldap
from django_auth_ldap.config import (
    LDAPSearch,
    GroupOfUniqueNamesType,
)

AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = False
AUTH_LDAP_SERVER_URI = 'ldaps://ldap01.corp.digitalreasoning.com'
AUTH_LDAP_BIND_DN = 'uid=binduser,ou=People,dc=digitalreasoning,dc=com'
AUTH_LDAP_BIND_PASSWORD = 'j9cHqQZFSOD'
AUTH_LDAP_REQUIRE_GROUP = ('cn=stackdio-user,ou=Group,'
                           'dc=digitalreasoning,dc=com')
AUTH_LDAP_USER_SEARCH = LDAPSearch('ou=People,dc=digitalreasoning,dc=com',
                                   ldap.SCOPE_SUBTREE,
                                   '(&(objectClass=Person)(uid=%(user)s))')
AUTH_LDAP_FIND_GROUP_PERMS = False
AUTH_LDAP_MIRROR_GROUPS = False
AUTH_LDAP_GROUP_TYPE = GroupOfUniqueNamesType()
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'ou=Group,dc=digitalreasoning,dc=com',
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfNames)')
AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    'is_superuser': 'cn=stackdio-admin,ou=Group,dc=digitalreasoning,dc=com',
    'is_staff': 'cn=stackdio-admin,ou=Group,dc=digitalreasoning,dc=com',
}
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
    ldap.OPT_X_TLS_NEWCTX: 0,
}
