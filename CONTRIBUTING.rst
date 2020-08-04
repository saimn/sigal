Filing issues
-------------

If you have an issue with sigal, the first step is to run::

    sigal build -fd -n 1

to get diagnostic information (debug mode, only one core). If you can identify
an image or video that is causing the issue, you can create a new directory
containing only this image/video and rerun ``sigal build -fd -n 1``.

Then, put the output into a gist/pastebin, and fill an issue on github.  You can
also try to get help via the ``#sigal`` IRC channel on freenode.

How To Contribute
-----------------

sigal is always open for suggestions and contributions by generous developers.
Here are a few tips to get you started.

Please:

- Obey `PEP 8`_ and `PEP 257`_.
- *Always* add tests and docs for your code.
- Add yourself to the AUTHORS file in an alphabetical fashion, and add your
  name to the license header of the files you modify.
- Write `good commit messages`_.
- Ideally, squash_ your commits, i.e. make your pull requests just one commit.
- Use a branch, it will be easier to squash or rebase on upstream's master.

Thank you for considering to contribute to sigal !


.. _squash: http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html
.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _PEP 257: http://www.python.org/dev/peps/pep-0257/
.. _good commit messages: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
