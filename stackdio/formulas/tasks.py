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


def clone_to_temp(formula):
    try:

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
                raise FormulaTaskException(
                    formula,
                    'Unable to clone provided URI. Are you sure this is '
                    'a git repository?')

            raise FormulaTaskException(
                formula,
                'An error occurred while importing formula.')

        # return the path where the repo is
        return repodir

    except Exception, e:
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')


def validate_specfile(formula, repodir):
    try:
        specfile_path = os.path.join(repodir, 'SPECFILE')
        if not os.path.isfile(specfile_path):
            raise FormulaTaskException(
                formula,
                'Formula did not have a SPECFILE. Each formula must define a '
                'SPECFILE in the root of the repository.')

        # Load and validate the SPECFILE
        with open(specfile_path) as f:
            specfile = yaml.safe_load(f)

        formula_title = specfile.get('title', '')
        formula_description = specfile.get('description', '')
        root_path = specfile.get('root_path', '')
        components = specfile.get('components', [])

        if not formula_title:
            raise FormulaTaskException(
                formula,
                "Formula SPECFILE 'title' field is required.")

        if not root_path:
            raise FormulaTaskException(
                formula,
                "Formula SPECFILE 'root_path' field is required.")

        # check root path location
        if not os.path.isdir(os.path.join(repodir, root_path)):
            raise FormulaTaskException(
                formula,
                'Formula SPECFILE \'root_path\' must exist in the formula. '
                'Unable to locate directory: {0}'.format(root_path))

        if not components:
            raise FormulaTaskException(
                formula,
                'Formula SPECFILE \'components\' field must be a non-empty '
                'list of components.')

        # Give back the components
        return formula_title, formula_description, root_path, components

    except Exception, e:
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')


def validate_component(formula, repodir, component):
    try:
        # check for required fields
        if 'title' not in component or 'sls_path' not in component:
            raise FormulaTaskException(
                formula,
                'Each component in the SPECFILE must contain a \'title\' '
                'and \'sls_path\' field.')

        # determine if the sls_path is valid...we're looking for either
        # a directory with an init.sls or an sls file of the same name
        # as the last location of the path
        component_title = component['title']
        sls_path = component['sls_path'].replace('.', '/')
        init_file = os.path.join(sls_path, 'init.sls')
        sls_file = sls_path + '.sls'
        abs_init_file = os.path.join(repodir, init_file)
        abs_sls_file = os.path.join(repodir, sls_file)

        if not os.path.isfile(abs_init_file) and \
                not os.path.isfile(abs_sls_file):
            raise FormulaTaskException(
                formula,
                'Could not locate an SLS file for component \'{0}\'. '
                'Expected to find either \'{1}\' or \'{2}\'.'
                .format(component_title, init_file, sls_file))
    except Exception, e:
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')


# TODO: Ignoring complexity issues
@celery.task(name='formulas.import_formula')  # NOQA
def import_formula(formula_id):
    try:
        formula = Formula.objects.get(pk=formula_id)
        formula.set_status(Formula.IMPORTING, 'Cloning and importing formula.')

        repodir = clone_to_temp(formula)

        root_dir = formula.get_repo_dir()

        if os.path.isdir(root_dir):
            raise FormulaTaskException(
                formula,
                'Formula root path already exists.')

        formula_title, formula_description, root_path, components = validate_specfile(formula, repodir)

        # update the formula title and description
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        # validate components
        for component in components:
            validate_component(formula, repodir, component)

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


        root_dir = formula.get_repo_dir()

        # move the cloned formula repository to a location known by salt
        # so we can start using the states in this formula
        shutil.move(repodir, root_dir)

        tmpdir = os.path.dirname(repodir)

        # remove tmpdir now that we're finished
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True
    except Exception, e:
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')


# TODO: Ignoring complexity issues
@celery.task(name='formulas.update_formula')  # NOQA
def update_formula(formula_id):
    try:
        formula = Formula.objects.get(pk=formula_id)
        formula.set_status(Formula.IMPORTING, 'Updating formula.')

        repodir = clone_to_temp(formula)

        formula_title, formula_description, root_path, components = validate_specfile(formula, repodir)

        old_components = formula.components.all()

        # Check for added or changed components
        added_components = []
        changed_components = []
        removed_components = []

        for component in components:

            # Check to see if the component was already in the formula
            exists = False
            for old_component in old_components:
                if component['sls_path'] == old_component.sls_path:
                    # If we find a matching sls path,
                    # update the associated title and description
                    changed_components.append(component)
                    exists = True
                    break

            # if not, set it to be added
            if not exists:
                added_components.append(component)

        # Check for removed components
        for old_component in old_components:

            # check if the old component is in the new formula
            exists = False
            for component in components:
                if component['sls_path'] == old_component.sls_path:
                    exists = True
                    break

            if not exists:
                removed_components.append(old_component)

        # Everything was validated, update the database
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        # validate new components
        for component in added_components:
            validate_component(formula, repodir, component)

        # validate changed components
        for component in changed_components:
            validate_component(formula, repodir, component)

        # Check to see if the removed components are used
        removal_errors = []
        for component in removed_components:
            blueprint_hosts = component.blueprinthostformulacomponent_set.all()
            if len(blueprint_hosts) is 0:
                component.delete()
            else:
                removal_errors.append(component.sls_path)

        if len(removal_errors) is not 0:
            errors = ', '.join(removal_errors)
            formula.set_status(
                Formula.COMPLETE,
                'Formula could not be updated.  The following components '
                'are used in blueprints: {0}.   '
                'Your formula was left unchanged.'.format(errors))
            return False

        # Add the new components
        for component in added_components:
            title = component['title']
            description = component.get('description', '')
            sls_path = component['sls_path']
            formula.components.create(title=title,
                                      sls_path=sls_path,
                                      description=description)

        # Update the other components
        for component in changed_components:
            sls_path = component['sls_path']
            to_change = formula.components.get(sls_path=sls_path)
            to_change.title = component['title']
            to_change.description = component.get('description', '')
            to_change.save()


        root_dir = formula.get_repo_dir()


        # Remove the old formula
        shutil.rmtree(root_dir)

        # move the cloned formula repository to a location known by salt
        # so we can start using the states in this formula
        shutil.move(repodir, root_dir)

        tmpdir = os.path.dirname(repodir)

        # remove tmpdir now that we're finished
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True

    except Exception, e:
        logger.exception(e)
        raise FormulaTaskException(
            formula,
            'An unhandled exception occurred.  Your formula was not changed')

