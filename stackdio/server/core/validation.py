VALID_PROTOCOLS = ('tcp', 'udp', 'icmp')


class ValidationErrors(object):
    REQUIRED_FIELD = 'Required field.'
    BOOLEAN_REQUIRED = 'Boolean type required.'
    OBJECT_REQUIRED = 'Object type required.'
    LIST_REQUIRED = 'List type required.'
    INT_REQUIRED = 'Non-negative integer required.'
    DECIMAL_REQUIRED = 'Non-negative decimal value required.'

    DUP_BLUEPRINT = 'A Blueprint with this value already exists.'
    DUP_HOST_TITLE = 'Duplicate title. Each host title must be unique.'
    MULTIPLE_COMPONENTS = 'Multiple components found.'

    STACKDIO_RESTRICTED_KEY = ('The __stackdio__ key is reserved for '
                               'system use.')

    DOES_NOT_EXIST = 'Object does not exist.'
    INVALID_INT = 'Value could not be converted to an integer.'
    MIN_HOSTS = 'Must have at least one host.'
    MIN_ONE = 'Must be greater than zero.'

    UNHANDLED_ERROR = 'An unhandled error occurred.'


class BaseValidator(object):

    def __init__(self, request):
        self.request = request
        self.data = request.DATA
        self._errors = {}

    def validate(self):
        return self._errors

    def set_error(self, key, msg):
        self._errors.setdefault(key, []).append(msg)

    def _validate_count(self, obj):
        e = {}
        if 'count' not in obj:
            e['count'] = ValidationErrors.REQUIRED_FIELD
        elif not isinstance(obj['count'], int):
            e['count'] = ValidationErrors.INT_REQUIRED
        elif obj['count'] <= 0:
            e['count'] = ValidationErrors.MIN_ONE
        return e
