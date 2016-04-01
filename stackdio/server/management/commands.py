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
import os
import shutil
import sys
import textwrap

import jinja2
import six
import yaml
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import get_random_string
from salt.utils import get_colors
from salt.version import __version__ as salt_version

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
        from stackdio.core.config import StackdioConfig
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
        for i in range(nl):
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
                    self.out('Invalid response. Must be one of {0}'.format(
                        choices),
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
        from pkg_resources import ResourceManager, get_provider
        provider = get_provider(package)
        if rp is None:
            return os.path.dirname(provider.module_path)
        return provider.get_resource_filename(ResourceManager(), rp)

    def render_template(self, tmpl, outfile=None, context=None):
        if context is None:
            context = {}

        tmpl = self.load_resource(tmpl)
        with open(tmpl) as f:
            t = jinja2.Template(f.read()).render(context)
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
            self.out('{0} = {1}'.format(
                question['attr'],
                self.answers[question['attr']]),
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
    CONFIG_DIR = os.path.expanduser('~/.stackdio')

    # Default config file
    CONFIG_FILE = os.path.join(CONFIG_DIR, 'config')

    def __init__(self, *args, **kwargs):
        super(InitCommand, self).__init__(*args, **kwargs)

        # TODO - why doesn't this work just putting it down with everything
        # else?
        # https://docs.python.org/2/library/threading.html#importing-in-threaded-code

        self.QUESTIONS = [{
            'attr': 'user',
            'short_desc': 'Which user will stackdio and salt run as?',
            'long_desc': ('This user will own services, files, etc related to '
                          'stackdio.'),
            'default': getpass.getuser(),
        }, {
            'attr': 'storage_root',
            'short_desc': 'Where should stackdio and salt store their data?',
            'long_desc': ('Root directory for stackdio to store its files, logs, '
                          'salt configuration, etc. We will attempt to create '
                          'this path if it does not already exist.'),
            'default': self.CONFIG_DIR,
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
                          'for more info.  You must include \'{salt_version}\' somewhere - '
                          'it will be replaced by the current version of the salt master.'),
            'default': 'stable archive/{salt_version}'
        }, {
            'attr': 'db_dsn',
            'short_desc': ('What database DSN should stackdio use to connect to '
                           'the DB?'),
            'long_desc': ('The database DSN the stackdio Django application will '
                          'use to acccess the database server. The server must be '
                          'running, the database must already exist, and the user '
                          'must have access to it.'),
            'default': 'mysql://stackdio:password@localhost:3306/stackdio',
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
            self.answers = self.stackdio_config()
        except ImproperlyConfigured:
            self.answers = {}

        # Let the user know we've changed the defaults by reusing the
        # existing config
        if self.answers:
            self.out()
            self.out('Existing configuration file found. Default values '
                     'for questions below will use existing values.',
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
        # create some directories we need
        dirs = (
            self.CONFIG_DIR,
            os.path.join(self.CONFIG_DIR, 'var/log/web'),
            os.path.join(self.CONFIG_DIR, 'var/log/supervisord'),
            os.path.join(self.CONFIG_DIR, 'var/run'),
        )

        for d in dirs:
            try:
                os.makedirs(d, mode=0o0755)
            except OSError:
                pass

        self.render_template('server/management/templates/config.jinja2',
                             self.CONFIG_FILE,
                             context=self.answers)
        self.out('stackdio configuration written to '
                 '{0}'.format(self.CONFIG_FILE),
                 Colors.INFO,
                 width=1024,
                 **self.INFO_INDENT)

        # grab a fresh copy of the config file to be used later
        self.config = self.stackdio_config()

    def _init_salt(self):
        if not os.path.isdir(self.config.salt_config_root):
            os.makedirs(self.config.salt_config_root)
            self.out('Created salt configuration directory at '
                     '{0}'.format(self.config.salt_config_root),
                     Colors.INFO,
                     width=1024,
                     **self.INFO_INDENT)

        # Render salt-master and salt-cloud configuration files
        self.render_template('server/management/templates/master.jinja2',
                             self.config.salt_master_config,
                             context=self.config)
        self.out('Salt master configuration written to '
                 '{0}'.format(self.config.salt_master_config),
                 Colors.INFO,
                 width=1024,
                 **self.INFO_INDENT)

        self.render_template('server/management/templates/cloud.jinja2',
                             self.config.salt_cloud_config,
                             context=self.config)
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
        from pwd import getpwnam
        try:
            getpwnam(answer)
        except KeyError:
            return False, 'User does not exist. Please try another user.\n'
        return True, ''

    def _validate_storage_root(self, question, path):
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
        from pwd import getpwnam
        user = self.answers['user']
        uid = getpwnam(user).pw_uid
        stat = os.stat(path)
        if stat.st_uid != uid:
            return False, 'Directory is not owned by {0} user.\n'.format(user)
        if not os.access(path, os.W_OK):
            return False, 'Directory is not writable.\n'
        return True, ''

    def _validate_db_dsn(self, question, dsn):
        from django.conf import settings
        if not settings.configured:
            settings.configure()

        from django.db.utils import load_backend
        from dj_database_url import parse

        db = parse(dsn)
        db['OPTIONS'] = {'connect_timeout': 3}

        # These are django defaults - there seems to be a bug in dj-database-url that causes an
        # exception if these keys are missing
        db['CONN_MAX_AGE'] = 0
        db['AUTOCOMMIT'] = True

        try:
            engine = load_backend(db['ENGINE']).DatabaseWrapper(db)
            engine.cursor()
        except KeyError:
            return False, 'Invalid DSN provided.\n'
        except Exception as e:
            return False, '{0}\n'.format(str(e))
        return True, ''


class ConfigCommand(BaseCommand):

    def run(self):
        config = self.stackdio_config()
        stackdio_root = self.load_resource()
        context = {
            'stackdio_root': stackdio_root,
            'storage_root': config.storage_root,
        }
        if self.args.type == 'stackdio':
            import json
            print(json.dumps(config, indent=4))
            return
        elif self.args.type == 'apache':
            context.update({
                'user': config.user,
                'with_ssl': self.args.with_ssl,
            })
            tmpl = 'server/management/templates/apache2.jinja2'
        elif self.args.type == 'nginx':
            context.update({
                'with_ssl': self.args.with_ssl
            })
            tmpl = 'server/management/templates/nginx.jinja2'
        elif self.args.type == 'supervisord':
            tmpl = 'server/management/templates/supervisord.jinja2'
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

    # Default directory holding the stackdio configuration
    CONFIG_DIR = os.path.expanduser('~/.stackdio')

    # Default config file
    CONFIG_FILE = os.path.join(CONFIG_DIR, 'config')

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

    def run(self):
        import sys
        import salt.scripts
        config = self.stackdio_config()

        args = [arg for arg in self.args[:] if '--config-dir' not in arg]
        args.insert(1, '--config-dir={0}'.format(config.salt_config_root))

        salt_cmd = self.args[0]
        salt_func = salt_cmd.replace('-', '_')

        # special cases
        if salt_cmd == 'salt':
            salt_func = 'salt_main'

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
