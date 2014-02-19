import jinja2
import os
import shutil
import sys

from stackdio.core.config import StackdioConfig
from django.utils.crypto import get_random_string
from salt.utils import get_colors

SALT_COLORS = get_colors()


class Colors(object):
    ENDC = SALT_COLORS['ENDC']
    BLACK = SALT_COLORS['DEFAULT_COLOR']
    ERROR = SALT_COLORS['RED_BOLD']
    WARN = SALT_COLORS['BROWN']
    INFO = SALT_COLORS['CYAN']
    PROMPT = SALT_COLORS['GREEN']
    VALUE = SALT_COLORS['BLUE']


class BaseCommand(object):

    def __init__(self, args):
        self.args = args

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

    def out(self, msg, color=Colors.BLACK, fp=sys.stdout):
        fp.write(color + msg + Colors.ENDC)

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
                    self.out('Invalid response. Must be one of {0}\n\n'
                             .format(choices), Colors.ERROR)
                    continue
                if not value and default is None:
                    self.out('Invalid response. Please provide a value.\n\n',
                             Colors.ERROR)
                    continue
                if not value:
                    value = default
                return value

        except (KeyboardInterrupt, EOFError):
            self.out('\nAborting.\n', Colors.ERROR)
            sys.exit(1)

    def load_resource(self, rp=None, package='stackdio'):
        '''
        Takes a relative path `rp`, and attempts to pull the full resource
        path using pkg_resources.
        '''
        from pkg_resources import ResourceManager, get_provider
        provider = get_provider(package)
        if rp is None:
            return provider.module_path
        return provider.get_resource_filename(ResourceManager(), rp)

    def render_template(self, tmpl, outfile, context={}):
        tmpl = self.load_resource(tmpl)
        with open(tmpl) as f:
            t = jinja2.Template(f.read())

        with open(outfile, 'w') as f:
            f.write(t.render(context))


class WizardCommand(BaseCommand):
    '''
    QUESTIONS is required. It's a list of tuples and of the format:
        (   index0: required
            Unique name for this question. This will be the key into
            the answers dictionary for storing the user's answers

            index1:
            A short description of the question.

            index2:
            A more detailed description of the question.

            index3:
            A default answer to provide to the user. This is either a string
            or a tuple of choices (strings)
        )

    After each question, an optional validator can be ran to make
    sure the response is ok. To do so define a method on the class:
        _validate_<NAME>(self, question, answers)
        where NAME is the unique name of the question;
    This method will receive the current question
    '''

    def __init__(self, args):
        self.args = args

        # Answers holds the values from each question. Each question
        # name must be unique.
        self.answers = {}

    def run(self):
        '''
        Iterate over the QUESTIONS attribute, prompting the user
        while recording and validating their answers.
        '''
        for question in self.QUESTIONS:
            attr, title, desc, default = question[:4]
            default = self.answers[attr] or default
            self.out('## {0}\n'.format(title), Colors.PROMPT)
            self.out('{0}\n'.format(desc), Colors.PROMPT)

            while True:
                value = self.prompt('', default)
                if not hasattr(self, '_validate_{0}'.format(attr)):
                    break
                func = getattr(self, '_validate_{0}'.format(attr))
                ok, msg = func(question, value)
                if ok:
                    break
                self.out(msg, Colors.ERROR)
            self.out('\n')
            self.answers[attr] = value

        self.out('Are the following values correct?\n', Colors.PROMPT)
        for question in self.QUESTIONS:
            self.out('    {0}\n'.format(
                self.answers[question[0]]),
                Colors.VALUE)
        self.out('\nWARNING: If you say no, we will abort without changing '
                 'anything!\n\n', Colors.ERROR)

        ok = self.prompt('Correct? ', default=('yes', 'no'))
        self.out('\n')

        if ok == 'no':
            self.out('Aborting.\n', Colors.ERROR)
            sys.exit(1)


class InitCommand(WizardCommand):
    # Default directory holding the stackdio configuration
    CONFIG_DIR = os.path.expanduser('~/.stackdio')

    # Default config file
    CONFIG_FILE = os.path.join(CONFIG_DIR, 'config')

    QUESTIONS = [
        ('user',
         'Which user will stackdio and salt run as?',
         'This user will own services, files, etc related to stackdio.',
         'stackdio'),
        ('storage_root',
         'Where should stackdio and salt store their data?',
         'Root directory for stackdio to store its files, logs, salt\n'
         'configuration, etc. It must exist and be owned by the user\n'
         'provided above.',
         '/var/lib/stackdio'),
        ('salt_bootstrap_script',
         'Which bootstrap script should salt-cloud use when launching VMs?',
         'When launching and bootstrapping machines using salt-cloud,\n'
         'what bootstrap script should be used? Typically, this should\n'
         'be left alone.',
         'bootstrap-salt'),
        ('salt_bootstrap_args',
         'Any special arguments for the bootstrap script?',
         'What arguments to pass to the bootstrap script above? For our\n'
         'purposes, we are enabling debug output for tracking down issues\n'
         'that may crop up during the bootstrap process. Override the\n'
         'defaults here. See http://bootstrap.saltstack.org for more info',
         '-K -D git 3a894d760699ab155bc63a3e35e6730f87cc7d8c'),
        ('db_dsn',
         'What database DSN should stackdio use to connect to the DB?',
         'The database DSN the stackdio Django application will use to\n'
         'acccess the database server. The server must be running, the\n'
         'database must already exist, and the user must have access to it.',
         'mysql://user:pass@localhost:3306/stackdio'),
    ]

    def pre_run(self):
        self.answers = StackdioConfig()

        # Let the user know we've changed the defaults by reusing the
        # existing config
        if self.answers:
            self.out('## WARNING: Existing configuration file found. Using '
                     'values as defaults.\n\n', Colors.WARN)

        # The template expects a django_secret_key, and if we don't have one
        # we'll generate one for the user automatically (using the logic
        # provided by Django)
        if not self.answers.get('django_secret_key'):
            chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            self.answers['django_secret_key'] = get_random_string(50, chars)

    def post_run(self):
        self._init_stackdio()
        self._init_salt()
        self.out('Finished\n', Colors.INFO)

    def _init_stackdio(self):
        # create config dir if it doesn't already exist
        if not os.path.isdir(self.CONFIG_DIR):
            os.makedirs(self.CONFIG_DIR, mode=0755)

        self.render_template('stackdio/management/templates/config.jinja2',
                             self.CONFIG_FILE,
                             context=self.answers)
        self.out('stackdio configuration written to {0}\n'.format(
            self.CONFIG_FILE), Colors.INFO)

        # grab a fresh copy of the config file to be used later
        self.config = StackdioConfig()

    def _init_salt(self):
        if not os.path.isdir(self.config.salt_config_root):
            os.makedirs(self.config.salt_config_root)
            self.out('Created salt configuration directory at '
                     '{0}\n'.format(self.config.salt_config_root), Colors.INFO)

        # Render salt-master and salt-cloud configuration files
        self.render_template('stackdio/management/templates/master.jinja2',
                             self.config.salt_master_config,
                             context=self.config)
        self.out('Salt master configuration written to {0}\n'.format(
            self.config.salt_master_config), Colors.INFO)

        self.render_template('stackdio/management/templates/cloud.jinja2',
                             self.config.salt_cloud_config,
                             context=self.config)
        self.out('Salt cloud configuration written to {0}\n'.format(
            self.config.salt_cloud_config), Colors.INFO)

        # Copy the salt directories needed
        saltdirs = self.load_resource('stackdio/management/saltdirs')
        for rp in os.listdir(saltdirs):
            path = os.path.join(saltdirs, rp)
            dst = os.path.join(self.config.salt_root, rp)

            # check for existing dst and skip it
            if os.path.isdir(dst):
                self.out('Salt configuration directory {0} already exists...'
                         'skipping.\n'.format(rp), Colors.WARN)
                continue

            shutil.copytree(path, dst)
            self.out('Copied salt configuration directory {0}.\n'.format(rp),
                     Colors.INFO)

    def _validate_user(self, question, answer):
        from pwd import getpwnam
        try:
            getpwnam(answer)
        except KeyError:
            return False, 'User does not exist. Please try another user.\n'
        return True, ''

    def _validate_storage_root(self, question, path):
        from pwd import getpwnam

        if not os.path.exists(path):
            return False, 'Directory does not exist.\n'
        if not os.path.isdir(path):
            return False, 'Path is not a directory.\n'

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

        try:
            engine = load_backend(db['ENGINE']).DatabaseWrapper(db)
            engine.cursor()
        except KeyError:
            return False, 'Invalid DSN provided.\n'
        except Exception, e:
            return False, '{0}\n'.format(str(e))
        return True, ''


class ConfigCommand(BaseCommand):

    def run(self):
        config = StackdioConfig()
        import json
        print(json.dumps(config, indent=4))


class SaltWrapperCommand(BaseCommand):

    def run(self):
        import sys
        import salt.scripts
        config = StackdioConfig()

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


class DjangoManageWrapperCommand(BaseCommand):

    def run(self):
        import sys
        sys.path.insert(0, '/home/stackdio/.virtualenvs/testing/lib/python2.6/site-packages')
        sys.path.insert(1, '/home/stackdio/.virtualenvs/testing/lib/python2.6/site-packages/stackdio-0.5a1-py2.6.egg')
        sys.path.insert(2, '/home/stackdio/.virtualenvs/testing/lib/python2.6/site-packages/stackdio-0.5a1-py2.6.egg/stackdio')
        sys.path.insert(3, '/home/stackdio/.virtualenvs/testing/lib/python2.6/site-packages/stackdio-0.5a1-py2.6.egg/stackdio/stackdio')
        from django.core.management import execute_from_command_line
        os.environ['DJANGO_SETTINGS_MODULE'] = 'stackdio.settings.development'
        print self.args
        execute_from_command_line(self.args)
