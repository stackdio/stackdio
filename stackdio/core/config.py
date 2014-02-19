import os
import yaml
from django.core.exceptions import ImproperlyConfigured


class StackdioConfig(dict):
    CONFIG_FILE = os.path.expanduser('~/.stackdio/config')
    REQUIRED_FIELDS = (
        'user',
        'db_dsn',
        'storage_root',
        'django_secret_key')

    def __init__(self, *args, **kwargs):
        self._load_stackdio_config()

    def _load_stackdio_config(self):
        if not os.path.isfile(self.CONFIG_FILE):
            raise ImproperlyConfigured(
                'Missing stackdio configuration file. To create the file, you '
                'may use `stackdio init`')
        with open(self.CONFIG_FILE) as f:
            config = yaml.safe_load(f)

        if not config:
            raise ImproperlyConfigured(
                'stackdio configuration file appears to be empty or not '
                'valid yaml.')

        errors = []
        for k in self.REQUIRED_FIELDS:
            if k not in config:
                errors.append('Missing parameter `{0}`'.format(k))

        if errors:
            msg = 'stackdio configuration errors:\n'
            for err in errors:
                msg += '  - {0}\n'.format(err)
            raise ImproperlyConfigured(msg)

        self.update(config)

        # additional helper attributes
        self.salt_root = os.path.join(self.storage_root)
        self.salt_config_root = os.path.join(self.salt_root, 'etc', 'salt')
        self.salt_master_config = os.path.join(self.salt_config_root, 'master')
        self.salt_cloud_config = os.path.join(self.salt_config_root, 'cloud')

        # defaults
        if not self.salt_master_log_level:
            self.salt_master_log_level = 'info'

    def __getattr__(self, k):
        return self.get(k)

    def __setattr__(self, k, v):
        self[k] = v

if __name__ == '__main__':
    config = StackdioConfig()
    print(config.user)
