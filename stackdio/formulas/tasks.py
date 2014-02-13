import celery
import envoy
import logging
import os
import shutil
import yaml
from tempfile import mkdtemp

from django.conf import settings

from formulas.models import Formula

logger = logging.getLogger(__name__)


class FormulaTaskException(Exception):
    def __init__(self, formula, error):
        formula.set_status(Formula.ERROR, error)
        super(FormulaTaskException, self).__init__(error)


@celery.task(name='formulas.import_formula')
def import_formula(formula_id):
    try:
        formula = Formula.objects.get(pk=formula_id)
        formula.set_status(Formula.IMPORTING, 'Cloning and importing formula.')

        # temporary directory to clone into so we can read the
        # SPECFILE and do some initial validation
        tmpdir = mkdtemp(prefix='stackdio-')
        reponame = formula.get_repo_name()
        repodir = os.path.join(tmpdir, reponame)

        # Clone the repository to the temp directory
        cmd = ' '.join([
            'git',
            'clone',
            formula.uri,
            repodir
        ])

        logger.debug('Executing command: {0}'.format(cmd))
        result = envoy.run(str(cmd))
        logger.debug('status_code: {0}'.format(result.status_code))

        if result.status_code != 0:
            logger.debug('std_out: {0}'.format(result.std_out))
            logger.debug('std_err: {0}'.format(result.std_err))

            if result.status_code == 128:
                raise FormulaTaskException(formula,
                    'Unable to clone provided URI. Are you sure this is a git repository?')

            raise FormulaTaskException(formula,
                'An error occurred while importing formula.')

        specfile_path = os.path.join(repodir, 'SPECFILE')
        if not os.path.isfile(specfile_path):
            raise FormulaTaskException(formula,
                'Formula did not have a SPECFILE. Each formula must define a '
                'SPECFILE in the root of the repository.')

        # Load and validate the SPECFILE
        with open(specfile_path) as f:
            specfile = yaml.safe_load(f)

        formula_title = specfile.get('title', '')
        formula_description = specfile.get('description', '')
        root_path = specfile.get('root_path', '')
        components = specfile.get('components', [])
        root_dir = os.path.join(settings.SALT_USER_STATES_ROOT,
                                formula.owner.username,
                                reponame)

        if os.path.isdir(root_dir):
            raise FormulaTaskException(formula,
                'Formula root path already exists.')

        if not formula_title:
            raise FormulaTaskException(formula,
                "Formula SPECFILE 'title' field is required.")

        if not root_path:
            raise FormulaTaskException(formula,
                "Formula SPECFILE 'root_path' field is required.")

        # update the formula title and description
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        # check root path location
        if not os.path.isdir(os.path.join(repodir, root_path)):
            raise FormulaTaskException(formula,
                "Formula SPECFILE 'root_path' must exist in the formula. "
                "Unable to locate directory: {0}".format(root_path))

        if not components:
            raise FormulaTaskException(formula,
                "Formula SPECFILE 'components' field must be a non-empty "
                "list of components.")

        # validate components
        for component in components:
            # check for required fields
            if 'title' not in component or 'sls_path' not in component:
                raise FormulaTaskException(formula, "Each component in the "
                    "SPECFILE must contain a 'title' and 'sls_path' field.")

            # determine if the sls_path is valid...we're looking for either
            # a directory with an init.sls or an sls file of the same name
            # as the last location of the path
            component_title = component['title']
            sls_path = component['sls_path'].replace('.', '/')
            init_file = os.path.join(sls_path, 'init.sls')
            sls_file = sls_path + '.sls'
            abs_init_file = os.path.join(repodir, init_file)
            abs_sls_file = os.path.join(repodir, sls_file)

            if not os.path.isfile(abs_init_file) and not os.path.isfile(abs_sls_file):
                raise FormulaTaskException(formula, "Could not locate an SLS "
                    "file for component '{0}'. Expected to find either '{1}' "
                    "or '{2}'.".format(component_title, init_file, sls_file))

        # all seems to be fine with the structure and mapping of the SPECFILE,
        # so now we'll build out the individual components of the formula
        # according to the SPECFILE
        for component in components:
            title = component['title']
            description = component.get('description', '')
            sls_path = component['sls_path']
            formula.components.create(title=title,
                                      sls_path=sls_path,
                                      description=description)

        # move the cloned formula repository to a location known by salt
        # so we can start using the states in this formula
        shutil.move(repodir, root_dir)

        # remove tmpdir now that we're finished
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)

        formula.set_status(Formula.COMPLETE, 'Import complete. Formula is now ready to be used.')

        return True
    except Exception, e:
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')

