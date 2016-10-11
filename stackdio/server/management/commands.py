# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from __future__ import print_function

import getpass
import json
import os
import pwd
import shutil
import socket
import sys
import textwrap

import django
import dj_database_url
import six
import yaml
from django.db.utils import load_backend
from django.utils.crypto import get_random_string
from jinja2 import Environment, PackageLoader
from pkg_resources import ResourceManager, get_provider
from salt.utils import get_colors
from salt.version import __version__ as salt_version
from stackdio.core.config import StackdioConfig, StackdioConfigException

raw_input = six.moves.input

SALT_COLORS = get_colors()


class Colors(object):
    ENDC = str(SALT_COLORS['ENDC'])
    BLACK = str(SALT_COLORS['DEFAULT_COLOR'])
    ERROR = str(SALT_COLORS['LIGHT_RED'])
    WARN = str(SALT_COLORS['YELLOW'])
    INFO = str(SALT_COLORS['CYAN'])
    PROMPT = str(SALT_COLORS['GREEN'])
    VALUE = str(SALT_COLORS['BLUE'])


class BaseCommand(object):
    ERROR_INDENT = dict(initial_indent='ERROR: ',
                        subsequent_indent='       ')
    WARNING_INDENT = dict(initial_indent='WARNING: ',
                          subsequent_indent='         ')
    INFO_INDENT = dict(initial_indent='INFO: ',
                       subsequent_indent='      ')

    def __init__(self, args, parser=None):
        self.args = args
        self.parser = parser
        self.env = Environment(loader=PackageLoader('stackdio.server.management', 'templates'))
        self.stackdio_config = StackdioConfig

    def __call__(self, *args, **kwargs):
        self.pre_run()
        self.run()
        self.post_run()

    def pre_run(self):
        pass

    def run(self):
        pass

    def post_run(self):
        pass

    def out(self, msg='', color=Colors.BLACK, fp=sys.stdout,
            wrap=True, nl=1, **kwargs):
        if wrap:
            msg = textwrap.fill(msg, **kwargs)
        fp.write(color + msg + Colors.ENDC)
        for _ in range(nl):
            fp.write('\n')

    def _get_prompt_msg(self, msg, default_value, choices):
        s = ''
        if msg:
            s = Colors.PROMPT + '{0} '.format(msg.strip())
        if choices:
            s += '{0}{1} '.format(Colors.VALUE, tuple(choices))
        elif default_value:
            s += '{0}[{1}] '.format(Colors.VALUE, default_value)
        s += Colors.ENDC
        return s

    def prompt(self, msg='', default=None):
        choices = None
        if isinstance(default, tuple):
            choices = default

        try:
            while True:
                value = raw_input(self._get_prompt_msg(msg,
                                                       default,
                                                       choices))

                if choices and value not in choices:
                    self.out('Invalid response. Must be one of {0}'.format(choices),
                             Colors.ERROR,
                             nl=2,
                             **self.ERROR_INDENT)
                    continue
                if not value and default is None:
                    self.out('Invalid response. Please provide a value.',
                             Colors.ERROR,
                             nl=2,
                             **self.ERROR_INDENT)
                    continue
                if not value:
                    value = default
                return value

        except (KeyboardInterrupt, EOFError):
            self.out('Aborting.', Colors.ERROR)
            sys.exit(1)

    def load_resource(self, rp=None, package='stackdio'):
        """
        Takes a relative path `rp`, and attempts to pull the full resource
        path using pkg_resources.
        """
        provider = get_provider(package)
        if rp is None:
            return os.path.dirname(provider.module_path)
        return provider.get_resource_filename(ResourceManager(), rp)

    def render_template(self, tmpl, outfile=None, context=None):
        if context is None:
            context = {}

        template = self.env.get_template(tmpl)

        t = template.render(context)

        if outfile:
            with open(outfile, 'w') as f:
                f.write(t)
        return t


class WizardCommand(BaseCommand):
    """
    QUESTIONS is required. It's a list of dict objects that look like:

        attr: required, the unique attribute name for this question that will
              be used as the key in the answers dictionary
        short_desc: required, a short description of this question
        long_desc: optional, a longer, more detailed description of the
                   question
        default: optional, a default answer to give the user. This may be
                 a string value or a tuple of string choices. If a tuple,
                 the user will be required to provide one of the available
                 choices.

    After each question, an optional validator can be ran to make
    sure the response is ok. To do so define a method on the class:
        _validate_<NAME>(self, question, answers)
        where NAME is the unique name of the question;
    This method will receive the current question
    """

    QUESTIONS = []

    def __init__(self, *args, **kwargs):
        super(WizardCommand, self).__init__(*args, **kwargs)

        # Answers holds the values from each question. Each question
        # name must be unique.
        self.answers = {}

    # TODO: Ignoring code complexity issues
    def run(self):  # NOQA
        """
        Iterate over the QUESTIONS attribute, prompting the user
        while recording and validating their answers.
        """
        for question in self.QUESTIONS:
            attr = question.get('attr')
            title = question.get('short_desc').format(**self.answers)
            desc = question.get('long_desc', '').format(**self.answers)
            default = question.get('default').format(**self.answers)
            true_value = question.get('true_value')
            require_true = question.get('require_true')

            if require_true and not self.answers.get(require_true):
                self.answers[attr] = None
                continue

            if not isinstance(default, tuple):
                default = self.answers.get(attr) or default

            self.out(title, Colors.PROMPT, initial_indent='## ')
            self.out(desc, Colors.PROMPT)

            while True:
                value = self.prompt('', default)
                if not hasattr(self, '_validate_{0}'.format(attr)):
                    break
                func = getattr(self, '_validate_{0}'.format(attr))
                ok, msg = func(question, value)
                if ok:
                    break
                self.out(msg,
                         Colors.ERROR,
                         **self.ERROR_INDENT)

            if true_value is not None:
                value = true_value == value
            self.answers[attr] = value
            self.out()

        self.out('Are the following values correct?', Colors.PROMPT)
        for question in self.QUESTIONS:
            self.out('{0} = {1}'.format(question['attr'], self.answers[question['attr']]),
                     Colors.VALUE,
                     initial_indent='    * ')
        self.out()
        self.out('If you say no, we will abort without writing any of your '
                 'configuration or saving any values you provided.',
                 Colors.WARN,
                 nl=2,
                 **self.WARNING_INDENT)

        ok = self.prompt('Correct? ', default=('yes', 'no'))

        if ok == 'no':
            self.out('Aborting.', Colors.ERROR)
            sys.exit(1)


class InitCommand(WizardCommand):
    # Default directory holding the stackdio configuration
    DOT_DIRECTORY = os.path.expanduser('~/.stackdio')

    # Default config file
    CONFIG_FILE = os.path.join(DOT_DIRECTORY, 'stackdio.yaml')

    def __init__(self, *args, **kwargs):
        super(InitCommand, self).__init__(*args, **kwargs)

        # TODO - why doesn't this work just putting it down with everything
        # else?
        # https://docs.python.org/2/library/threading.html#importing-in-threaded-code

        self.QUESTIONS = [{
            'attr': 'user',
            'short_desc': 'Which user will salt run as?',
            'long_desc': 'This user will own services, files, etc related to salt.',
            'default': getpass.getuser(),
        }, {
            'attr': 'server_url',
            'short_desc': 'What is the url that should be used to access the stackd.io webserver?',
            'long_desc': 'This is used to build urls in notifications that get sent.',
            'default': 'http://{}'.format(socket.getfqdn()),
        }, {
            'attr': 'database_url',
            'short_desc': 'What is the URL for your database?',
            'long_desc': ('stackd.io needs a relational database to store data in.  '
                          'The server must be running, the database must already exist, '
                          'and the user must have access to it.  See '
                          'https://github.com/kennethreitz/dj-database-url for more information '
                          'about how to construct this url.'),
            'default': 'postgres://stackdio:password@localhost:5432/stackdio',
        }, {
            'attr': 'celery_broker_url',
            'short_desc': 'What is the url of the celery broker?',
            'long_desc': ('Celery needs a broker to get task information from stackd.io.  '
                          'This can be redis, rabbitmq, or many other options.  '
                          'See http://docs.celeryproject.org/en/latest/getting-started/brokers/ '
                          'for more information.  If you are using redis for both celery and '
                          'caching, it is recommended to use different DB numbers for each.'),
            'default': 'redis://localhost:6379/0',
        }, {
            'attr': 'redis_url',
            'short_desc': 'What is the url of your redis server?',
            'long_desc': ('Redis is used as the cache backend for stackd.io.  '
                          'If you are using redis for both celery and caching, '
                          'it is recommended to use different DB numbers for each.'),
            'default': 'redis://localhost:6379/1',
        }, {
            'attr': 'salt_master_fqdn',
            'short_desc': 'What is the fqdn of your salt-master server?',
            'long_desc': 'stackd.io needs to know where your salt-master is running.',
            'default': socket.getfqdn(),
        }, {
            'attr': 'storage_dir',
            'short_desc': 'Where should stackdio and salt store their data?',
            'long_desc': ('Root directory for stackdio to store its files, '
                          'salt configuration, etc. We will attempt to create '
                          'this path if it does not already exist.'),
            'default': os.path.join(self.DOT_DIRECTORY, 'storage'),
        }, {
            'attr': 'log_dir',
            'short_desc': 'Where should stackdio and salt store their logs?',
            'long_desc': ('Root directory for stackdio to store its logs.  '
                          'We will attempt to create this path if it does not already exist.'),
            'default': os.path.join(self.DOT_DIRECTORY, 'logs'),
        }, {
            'attr': 'salt_bootstrap_script',
            'short_desc': ('Which bootstrap script should salt-cloud use when '
                           'launching VMs?'),
            'long_desc': ('When launching and bootstrapping machines using '
                          'salt-cloud, what bootstrap script should be used? '
                          'Typically, this should be left alone.'),
            'default': 'bootstrap-salt',
        }, {
            'attr': 'salt_bootstrap_args',
            'short_desc': 'Any special arguments for the bootstrap script?',
            'long_desc': ('What arguments to pass to the bootstrap script above? '
                          'Override the defaults here. See http://bootstrap.saltstack.org '
                          'for more info.  You must include \'{{salt_version}}\' somewhere - '
                          'it will be replaced by the current version of the salt master.'),
            'default': 'stable {{salt_version}}'
        }, {
            'attr': 'create_ssh_users',
            'short_desc': 'Should stackd.io create ssh user accounts on launched stacks?',
            'long_desc': ('When machines are launched and provisioned with core '
                          'functionality, stackd.io will create users on the '
                          'machine and add the authenticated stackd.io user\'s '
                          'public RSA key so they may SSH in to their machines. '
                          'This setting allows you to turn this feature off in the '
                          'case where you use some other external authentication '
                          'system, such as IPA or Active Directory.\n'
                          'NOTE: This is just a default value.  It can be overridden '
                          'on a per-stack or per-blueprint basis.'),
            'default': 'true',
        }]

    def pre_run(self):
        try:
            self.answers = self.stackdio_config(self.CONFIG_FILE)
        except StackdioConfigException:
            self.answers = {}

        # Let the user know we've changed the defaults by reusing the
        # existing config
        if self.answers:
            self.out()
            self.out('Existing configuration file found. Default values '
                     'for questions below will use existing values, and '
                     'the file will *NOT* be re-written.  If you wish to '
                     'modify your settings, change the config file manually.',
                     Colors.WARN,
                     nl=2,
                     **self.WARNING_INDENT)

        # The template expects a django_secret_key, and if we don't have one
        # we'll generate one for the user automatically (using the logic
        # provided by Django)
        if not self.answers.get('django_secret_key'):
            chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            self.answers['django_secret_key'] = get_random_string(50, chars)

    def post_run(self):
        self._init_stackdio()
        self._init_salt()
        self.out('Finished', Colors.INFO)

    def _init_stackdio(self):
        # only write config if it wasn't already written before
        if not os.path.isfile(self.CONFIG_FILE):
            self.render_template('stackdio.yaml',
                                 self.CONFIG_FILE,
                                 context=self.answers)
            self.out('stackdio configuration written to '
                     '{0}'.format(self.CONFIG_FILE),
                     Colors.INFO,
                     width=1024,
                     **self.INFO_INDENT)

        # grab a fresh copy of the config file to be used later
        self.config = self.stackdio_config()

        # create some directories we need
        dirs = (
            os.path.join(self.config.log_dir, 'web'),
            os.path.join(self.config.log_dir, 'supervisord'),
            os.path.join(self.config.storage_dir, 'run'),
        )

        for d in dirs:
            if not os.path.isdir(d):
                os.makedirs(d)

    def _init_salt(self):
        if not os.path.isdir(self.config.salt_config_root):
            os.makedirs(self.config.salt_config_root)
            self.out('Created salt configuration directory at '
                     '{0}'.format(self.config.salt_config_root),
                     Colors.INFO,
                     width=1024,
                     **self.INFO_INDENT)

        salt_config = self.config.copy()

        # Put the user in the context
        salt_config['user'] = self.answers['user']

        # Render salt-master and salt-cloud configuration files
        self.render_template('salt/master',
                             self.config.salt_master_config,
                             context=salt_config)
        self.out('Salt master configuration written to '
                 '{0}'.format(self.config.salt_master_config),
                 Colors.INFO,
                 width=1024,
                 **self.INFO_INDENT)

        self.render_template('salt/cloud',
                             self.config.salt_cloud_config,
                             context=salt_config)
        self.out('Salt cloud configuration written to '
                 '{0}'.format(self.config.salt_cloud_config),
                 Colors.INFO,
                 width=1024,
                 **self.INFO_INDENT)

        # Copy the salt directories needed
        saltdirs = self.load_resource('server/management/saltdirs')
        for rp in os.listdir(saltdirs):
            path = os.path.join(saltdirs, rp)
            dst = os.path.join(self.config.salt_root, rp)

            # check for existing dst and skip it
            if os.path.isdir(dst):
                self.out('Salt configuration directory {0} already exists...'
                         'skipping.'.format(rp),
                         Colors.WARN,
                         width=1024,
                         **self.WARNING_INDENT)
                continue

            shutil.copytree(path, dst)
            self.out('Copied salt configuration directory {0} to '
                     '{1}'.format(rp, dst),
                     Colors.INFO,
                     width=1024,
                     **self.INFO_INDENT)

    def _validate_user(self, question, answer):
        try:
            pwd.getpwnam(answer)
        except KeyError:
            return False, 'User does not exist. Please try another user.\n'
        return True, ''

    def _validate_storage_dir(self, question, path):
        if not os.path.isabs(path):
            return False, ('Relative paths are not allowed. Please provide '
                           'the absolute path to the storage directory.')
        if os.path.isdir(path):
            self.out()
            self.out('Directory already exists. stackd.io will manage its '
                     'data in this location, and as such we cannot guarantee '
                     'that any files or directories already located here '
                     'are safe from removal or modification. Please backup '
                     'anything important!',
                     Colors.WARN,
                     **self.WARNING_INDENT)
        else:
            try:
                os.makedirs(path)
            except Exception:
                return False, ('Directory did not exist and we could not '
                               'create it. Make sure appropriate permissions '
                               'are set.')

        # Check ownership
        user = self.answers['user']
        uid = pwd.getpwnam(user).pw_uid
        stat = os.stat(path)
        if stat.st_uid != uid:
            return False, 'Directory is not owned by {0} user.\n'.format(user)
        if not os.access(path, os.W_OK):
            return False, 'Directory is not writable.\n'
        return True, ''

    def _validate_database_url(self, question, url):
        # Ensure django is setup
        django.setup()

        try:
            db = dj_database_url.parse(url)
        except KeyError:
            return False, 'Failed to parse database URL.\n'

        options = {}

        if 'sqlite' not in db['ENGINE']:
            options['connect_timeout'] = 3

        db['OPTIONS'] = options

        # These are django defaults - the cursor() call craps out if these are missing.
        db['AUTOCOMMIT'] = True
        db['TIME_ZONE'] = None

        try:
            engine = load_backend(db['ENGINE']).DatabaseWrapper(db)
            engine.cursor()
        except KeyError:
            return False, 'Invalid database URL provided.\n'
        except Exception as e:
            return False, '{0}\n'.format(str(e))
        return True, ''


class ConfigCommand(BaseCommand):

    def run(self):
        config = self.stackdio_config()
        context = {
            'storage_dir': config.storage_dir,
        }
        if self.args.type == 'stackdio':
            print(json.dumps(config, indent=4))
            return
        elif self.args.type == 'nginx':
            context.update({
                'with_ssl': self.args.with_ssl
            })
            tmpl = 'nginx.conf'
        elif self.args.type == 'supervisord':
            tmpl = 'supervisord.conf'
            context.update({
                'with_gunicorn': self.args.with_gunicorn,
                'with_celery': self.args.with_celery,
                'with_salt_master': self.args.with_salt_master,
            })
        else:
            self.out('Unknown config type: {0}'.format(self.args.type),
                     Colors.ERROR,
                     nl=2,
                     **self.ERROR_INDENT)
            self.parser.print_help()
            return

        print(self.render_template(tmpl, context=context))


class UpgradeSaltCommand(BaseCommand):

    def run(self):

        self.out('NOTE: This command WILL NOT upgrade your version of salt-master.  '
                 'It will only upgrade the version of salt that is '
                 'installed on minions by changing your bootstrap args so that all '
                 'minions match the master version. You are highly advised NOT '
                 'to upgrade your salt version while you have running stacks, '
                 'as this may cause minion-master compatibility issues.  This '
                 'command will NOT stop you from upgrading while you have '
                 'running stacks, so proceed with caution.', Colors.WARN)

        val = self.prompt('Are you sure you would like to do this? (y|n) ')

        if val not in ('y', 'Y'):
            self.out('Aborting.  Your salt version was not upgraded.',
                     Colors.ERROR)
            return

        self.out('Updating config files...', nl=0)
        sys.stdout.flush()

        config = self.stackdio_config()

        new_args = config.salt_bootstrap_args.format(salt_version=salt_version)

        for profile_config in os.listdir(config.salt_profiles_dir):
            slug = '.'.join(profile_config.split('.')[:-1])

            prof_file = os.path.join(config.salt_profiles_dir, profile_config)
            with open(prof_file, 'r') as f:
                profile_yaml = yaml.safe_load(f)

            # Update the script and the args
            profile_yaml[slug]['script'] = config.salt_bootstrap_script
            profile_yaml[slug]['script_args'] = new_args

            with open(prof_file, 'w') as f:
                yaml.safe_dump(profile_yaml, f, default_flow_style=False)

        self.out('Done!')


class SaltWrapperCommand(BaseCommand):

    COMMANDS = {
        'salt': 'salt_main',
        'salt-api': 'salt_api',
        'salt-call': 'salt_call',
        'salt-cloud': 'salt_cloud',
        'salt-cp': 'salt_cp',
        'salt-key': 'salt_key',
        'salt-master': 'salt_master',
        'salt-minion': 'salt_minion',
        'salt-proxy': 'salt_proxy_minion',
        'salt-run': 'salt_run',
        'salt-ssh': 'salt_ssh',
        'salt-syndic': 'salt_syndic',
        'spm': 'salt_spm',
    }

    def run(self):
        import salt.scripts
        config = self.stackdio_config()

        args = [arg for arg in self.args[:] if '--config-dir' not in arg]
        args.insert(1, '--config-dir={0}'.format(config.salt_config_root))

        salt_cmd = self.args[0]
        salt_func = self.COMMANDS[salt_cmd]

        if not hasattr(salt.scripts, salt_func):
            raise RuntimeError(
                'Salt function {0} is not available.'.format(salt_func))
        salt_func = getattr(salt.scripts, salt_func)

        # argv trickery for salt commands
        sys.argv = args

        # execute the salt command
        salt_func()


class CeleryWrapperCommand(BaseCommand):

    def run(self):
        from stackdio.server.celery import app
        app.start(self.args)


class DjangoManageWrapperCommand(BaseCommand):

    def run(self):
        # Just default to production - if it's already set to something else, use that
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackdio.server.settings.production')

        # Import the needed arg
        from django.core.management import execute_from_command_line
        execute_from_command_line(self.args)
