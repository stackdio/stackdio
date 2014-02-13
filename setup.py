import os
import sys
from setuptools import setup, find_packages

if float("%d.%d" % sys.version_info[:2]) < 2.6:
    print('Your Python version {0}.{1}.{2} is not supported.'.format(
        *sys.version_info[:3]))
    print('stackdio requires Python 2.6 or newer.')
    sys.exit(1)

# Used later in load_requirements()
REQUIREMENTS = []
DEPENDENCY_LINKS = []

# Packages to exclude when using `find_packages` from setuptools
# See: http://pythonhosted.org/setuptools/setuptools.html#using-find-packages
EXCLUDE_FROM_PACKAGES = []

# Grab the current version from our stackdio package
VERSION = __import__('stackdio').get_version()

# Short and long descriptions for our package
SHORT_DESCRIPTION = ('A cloud deployment, automation, and orchestration '
                     'platform for everyone.')
LONG_DESCRIPTION = SHORT_DESCRIPTION

# If we have a README.md file, use its contents as the long description
if os.path.isfile('README.md'):
    with open('README.md') as f:
        LONG_DESCRIPTION = f.read()


def load_requirements(filepath):
    '''
    Build the list of requirements based on our requirements.txt
    that we use when installing dependencies via pip.
    '''
    cwd = os.path.dirname(filepath)
    with open(filepath) as f:
        for line in f.readlines():
            # skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # '-r' will require another file with requirements in it
            # so we pull off the -r and make a recursive call to
            # read in the new file
            if line.startswith('-r'):
                _, fp = line.strip().split(' ')
                if cwd:
                    fp = os.path.join(cwd, fp)
                load_requirements(fp)
                continue

            # -e signifies that we want to clone from a VCS, so we split
            # the -e off and are left with a URI. The URI must have an #egg
            # fragment with a value of <package>[-ver] (version is optional)
            # and the package must be the exact name of the package being
            # installed substituting underscores for hyphens. For example,
            # the package 'django_query_transform' is imported with the
            # underscores, but installed with hypens 'django-query-transform'.
            # The code will replace those underscores with hyphens and
            # add the package name to the list of requirements as well
            # as adding the URI to the list of dependency links so setup
            # can find and clone the package we need.
            if line.startswith('-e'):
                # strip the -e and find the URI
                _, uri = line.strip().split('-e ')
                # find the package name and replace underscores
                _, pkg = uri.strip().split('#egg=')
                pkg = pkg.replace('_', '-')
                # add the URI to dependency links and new package name
                # to the list of requirements
                DEPENDENCY_LINKS.append(uri)
                REQUIREMENTS.append(pkg)
                continue

            # regular style of requirements are simply added to the list
            # of requirements
            REQUIREMENTS.append(line.strip())

# build our list of requirements and dependency links based on our
# requirements.txt file
load_requirements('requirements.txt')

# Call the setup method from setuptools that does all the heavy lifting
# of packaging stackdio
setup(
    name='stackdio',
    version=VERSION,
    url='http://stackd.io',
    author='Digital Reasoning Systems, Inc.',
    author_email='info@stackd.io',
    description=SHORT_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license='Apache 2.0',
    include_package_data=True,
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    zip_safe=False,
    install_requires=REQUIREMENTS,
    dependency_links=DEPENDENCY_LINKS,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
    ],
    entry_points={'console_scripts': [
        'stackdio = stackdio.scripts.stackdio:main'
    ]}
)
