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

Install additional dependencies for development (Sphinx, pytest), and optional
dependencies::

    pip install -e .\[all,tests\]

Building the docs
-----------------

- Using tox_, run ``tox -e doc``
- Or ``make html`` in the ``docs/`` directory.

Running the test suite
----------------------

- Using tox_, run ``tox -e py37`` (replacing ``py37`` with your Python version
  if needed).

.. _tox: https://tox.readthedocs.io/
.. _virtualenv: https://virtualenv.pypa.io/

Building the test gallery
-------------------------

- Using tox_, run ``tox -e demo``
