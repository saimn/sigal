=========================
 Contributing guidelines
=========================

.. include:: ../CONTRIBUTING.rst

Setting up the development environment
--------------------------------------

 Using a virtualenv_::

    git clone https://github.com/saimn/sigal.git
    cd sigal
    virtualenv venv
    . venv/bin/activate

Install sigal in development mode::

    pip install -e .

Install additional dependencies for development (Sphinx, ...)::

    pip install -r requirements.txt

Building the docs
-----------------

- Run ``make docs`` (or ``make html`` in the ``docs/`` directory).

Running the test suite
----------------------

- Run ``make test`` (or ``pytest``).
- Run ``make coverage`` to get the coverage report.
- Using tox_ you can also run the tests on multiple versions of python.

.. _tox: https://tox.readthedocs.io/
.. _virtualenv: https://virtualenv.pypa.io/
