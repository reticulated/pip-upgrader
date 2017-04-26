"""
pip-upgrade

Usage:
  pip-upgrade [<requirements_file>] ... [--prerelease] [-p=<package>...] [--dry-run]

Arguments:
    requirements_file       The requirement FILE, or WILDCARD PATH to multiple files.
    --prerelease            Include prerelease versions for upgrade, when querying pypi repositories.
    -p <package>            Pre-choose which packages tp upgrade. Skips any prompt.
    -dry-run                Run all the command logic, except it doesn't install new packages neither replace the version in txt files.


Examples:
  pip-upgrade             # auto discovers requirements file
  pip-upgrade requirements.txt  
  pip-upgrade requirements/dev.txt requirements/production.txt
  pip-upgrade requirements.txt -p django -p celery
  pip-upgrade requirements.txt -p all
  pip-upgrade requirements.txt --dry-run  # run everything as a simulation (don't do the actual upgrade)
    
Help:
  Interactively upgrade packages from requirements file, and also update the pinned version from requirements file(s). 
  If no requirements are given, the command attempts to detect the requirements file(s) in the current directory.
  
  https://github.com/simion/pip-upgrader
"""
from __future__ import print_function
from colorclass import Windows, Color
from docopt import docopt

from pip_upgrader.packages_detector import PackagesDetector
from pip_upgrader.packages_interactive_selector import PackageInteractiveSelector
from pip_upgrader.packages_status_detector import PackagesStatusDetector
from pip_upgrader.packages_upgrader import PackagesUpgrader
from pip_upgrader.requirements_detector import RequirementsDetector
from . import __version__ as VERSION


def main():
    """ Main CLI entrypoint. """
    options = docopt(__doc__, version=VERSION)
    Windows.enable(auto_colors=True, reset_atexit=True)

    try:
        # 1. detect requirements files
        filenames = RequirementsDetector(options['<requirements_file>']).get_filenames()
        print(Color('{{autoyellow}}Found valid requirements file(s):{{/autoyellow}} '
                    '{{autocyan}}\n{}{{/autocyan}}'.format('\n'.join(filenames))))

        # 2. detect all packages inside requirements
        packages = PackagesDetector(filenames).get_packages()

        # 3. query pypi API, see which package has a newer version vs the one in requirements (or current env)
        packages_status_map = PackagesStatusDetector(packages).detect_available_upgrades(options)

        # 4. [optionally], show interactive screen when user can choose which packages to upgrade
        selected_packages = PackageInteractiveSelector(packages_status_map, options).get_packages()

        # 5. having the list of packages, do the actual upgrade and replace the version inside all filenames
        upgraded_packages = PackagesUpgrader(selected_packages, filenames, options['--dry-run']).do_upgrade()

        print(Color('{{autogreen}}Successfully upgraded (and updated requirements) for the following packages: '
                    '{}{{/autogreen}}'.format(','.join([package['name'] for package in upgraded_packages]))))
        if options['--dry-run']:
            print(Color('{automagenta}Actually, no, because this was a simulation using --dry-run{/automagenta}'))

    except KeyboardInterrupt:
        print(Color('{autored}Upgrade cancelled.{/autored}'))


