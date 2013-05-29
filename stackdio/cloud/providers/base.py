import os
import logging
import collections

from django.conf import settings

logger = logging.getLogger(__name__)

class BaseCloudProvider(object):
    
    REQUIRED_MESSAGE = 'This field is required.'

    # SHORT_NAME - required
    # Must correspond to a salt-cloud provider type (e.g, 'aws' or 
    # 'rackspace')
    SHORT_NAME = None

    # LONG_NAME - required
    # The human readable version of the SHORT_NAME (e.g, 'Amazon
    # Web Services' or 'Rackspace')
    LONG_NAME = None

    def __init__(self, obj=None, *args, **kwargs):

        # The `obj` attribute is the Django ORM object for this cloud 
        # provider instance. See models.py for more information.
        self.obj = obj

        # `provider_storage` is the location where provider implementations
        # should be writing their files to. If implementations are written
        # elsewhere, there's no guarantee that it will work later, be backed
        # up, etc.
        self.provider_storage = os.path.join(settings.FILE_STORAGE_DIRECTORY,
                                             'cloud',
                                             obj.slug) if self.obj else None

        # make sure the storage directory is available
        if self.provider_storage and \
           not os.path.isdir(self.provider_storage):
            os.makedirs(self.provider_storage)

    @classmethod
    def get_provider_choice(self):
        '''
        Should return a two-element tuple of the short and long name of the 
        provider type. This should be what the choices attribute on a
        model field is expected (e.g., ('db_value', 'Label') )
        '''

        if not hasattr(self, 'SHORT_NAME') or not self.SHORT_NAME:
            raise AttributeError('SHORT_NAME must exist and be a string.')

        if not hasattr(self, 'LONG_NAME') or not self.LONG_NAME:
            raise AttributeError('LONG_NAME must exist and be a string.')

        return (self.SHORT_NAME, self.LONG_NAME)

    @classmethod
    def get_required_fields(self):
        '''
        Return the fields required in the data dictionary for 
        `get_provider_data` and `validate_provider_data`
        '''
        raise NotImplementedError()

    @classmethod
    def get_provider_data(self, data, files):
        '''
        Takes a dict of values provided by the user (most likely from the 
        request data) and returns a new dict of info that's specific to
        the provider type you're implementing. The returned dict will be
        used in the yaml config written for salt cloud.

        `files` is a list of files that might have been uploaded to the 
        API that is available at this time. Each provider implementation
        must make sure that any files are written to disk and referenced
        properly in the result dict for salt cloud.
        
        See Salt Cloud documentation for more info on what needs to be in 
        this return dict for each provider.
        '''
        raise NotImplementedError()

    @classmethod
    def validate_provider_data(self, data, files):
        '''
        Checks that the keys defined in `get_required_fields` are in the
        given `data` dict. This merely checks that they are there and the
        values aren't empty. Override for any additional validation
        required.
        '''
        errors = collections.defaultdict(list)

        for key in self.get_required_fields():
            if not data.get(key):
                errors[key].append(self.REQUIRED_MESSAGE)

        return len(errors) == 0, errors
