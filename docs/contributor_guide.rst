Contributor Guidelines
======================

We're hopeful that you'll find value in using stackd.io along with your
existing tools to manage your infrastructure. We're also hopeful that
you'll find ways to help contribute. Either through finding and
reporting bugs, providing new features, or even getting your hands dirty
and contributing some code or docs. However you feel comfortable
contributing, we offer a few helpful guidelines to make it that much
easier.

    Note that stackd.io is built on SaltStack, and we believe that its
    community will find stackd.io useful. As such, we're trying to stay
    close to the conventions and guidelines they've adopted to make it
    easier for folks in that community to help out -- and we've borrowed
    from the `SaltStack Development
    guide <http://docs.saltstack.com/topics/development/hacking.html>`__
    :)

Filing issues and feature requests
==================================

The process for filing issues and feature requests is described in the
:doc:`contact` page.

Contributing Code
=================

Since we're using Github, the recommended workflow for fixing bugs,
adding features, or modifying documentation is to fork and submit pull
requests. The process is pretty straightforward, but if you're
unfamiliar with Github, take some time to browse through `Github's
Help <https://help.github.com/>`__.

In a nutshell, we'll need you to:

-  fork the stackd.io project into your personal account
   [`Tutorial <https://help.github.com/articles/fork-a-repo>`__\ ]
-  make the necessary changes to the code/docs and issue a pull request.
   [`Tutorial <https://help.github.com/articles/using-pull-requests/>`__\ ]
-  keep your local fork in sync with the parent stackd.io repository to
   minimize the chance of merge conflicts.
   [`Tutorial <https://help.github.com/articles/syncing-a-fork>`__\ ]
-  and, if you're working on multiple things or your changes are going
   to be somewhat large, it's generally recommended to create a branch
   for each piece of work you're doing.
   [`Tutorial <https://help.github.com/articles/creating-and-deleting-branches-within-your-repository>`__\ ]

    NOTE: SaltStack has a `great
    guide <http://docs.saltstack.com/topics/development/hacking.html>`__
    on how to work within their project and it mostly applies to
    stackd.io as well

Pull request guidelines
=======================

CLA
---

Contribution to stackd.io requires a CLA before pull requests will be
merged. This is currently handled manually by the repo admins, but may
be handled by a bot in the future.

Branch name
-----------

The branch name that the pull request originates from should start with
either ``feature/`` or ``bugfix/``, depending on its contents. The rest
of the branch name should describe the contents of the patch, preferably
by being an Issue#. Issue#'s are required for ``bugfix/`` branches.

Code style and quality
----------------------

PEP8 compatibility
~~~~~~~~~~~~~~~~~~

All pull requests must meet PEP8 compatibility

Tests
-----

Pull requests will be easier to review and understand if they contain
automated tests for the functionality changed. As such, pull requests
with tests are more likely to be accepted more quickly.
