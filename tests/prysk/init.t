Check init command:

  $ sigal init
  Sample config file created: sigal.conf.py

Check that it fails if the file already exists:

  $ sigal init
  Found an existing config file, will abort to keep it safe.
  [1]

Clean up:
  $ rm sigal.conf.py
