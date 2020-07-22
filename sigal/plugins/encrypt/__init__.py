"""
Plugin to protect gallery by encrypting image files using a password.

Options::

    encrypt_options = {
        'password': 'password',
        'ask_password': False,
        'gcm_tag': 'randomly_generated',
        'kdf_salt': 'randomly_generated',
        'kdf_iters': 10000,
    }

- ``password``: The password used to encrypt the images on gallery build,
  and decrypt them when viewers access the gallery. No default value. You must
  specify a password.
- ``ask_password``: Whether or not viewers are asked for the password to view
  the gallery. If set to ``False``, the password will be present in the HTML
  files so the images are decrypted automatically. Defaults to ``False``.
- ``gcm_tag``, ``kdf_salt``, ``kdf_iters``: Cryptographic parameters used when
  encrypting the files. ``gcm_tag``, ``kdf_salt`` are meant to be randomly
  generated, ``kdf_iters`` defaults to 10000. Do not specify them in the config
  file unless you have good reasons to do so.

Note: The plugin caches the cryptographic parameters (but not the password)
after the first build, so that incremental builds can share the same
credentials.  DO NOT CHANGE THE PASSWORD OR OTHER CRYPTOGRAPHIC PARAMETERS ONCE
A GALLERY IS BUILT, or there will be inconsistency in encrypted files and
viewers will not be able to see some of the images any more.

.. _compatibility-with-encrypt:

Compatibility with other plugins:

- ``zip_gallery``: if you enable both this plugin and the ``zip_gallery``
  plugin, the generated zip archives will contain encrypted images, which is
  generally meaningless since viewers cannot easily decrypt them outside
  a browser.

"""

from .encrypt import register
