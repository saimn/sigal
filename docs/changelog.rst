===========
 Changelog
===========

Version 0.4.1
~~~~~~~~~~~~~

Released on 2013-07-19.

- Fix a bug with unicode paths and filenames.
- Update colorbox to 1.4.26
- Add links to the original images.

Version 0.4.0
~~~~~~~~~~~~~

Released on 2013-06-12.

- Add a setting to disable the writing of HTML files.
- Use Pilkit.
- Remove multiprocessing.
- Add new settings for the source and destination directories.
- All meta-data are available in the templates.
- Galleria theme is now responsive
- Add a setting to choose the pilkit processor used to resize the images.

Version 0.3.3
~~~~~~~~~~~~~

Released on 2013-03-20.

- Catch exception when PIL fails to read the exif metadata.

Version 0.3.2
~~~~~~~~~~~~~

Released on 2013-03-14.

- Bugfix for PNG files which don't have exif metadata.
- Move unit tests to py.test.
- Fix images path in colorbox theme.
- Group package meta in a module.

Version 0.3.1
~~~~~~~~~~~~~

Released on 2013-03-11.

- Fix the path of the sample config file (which was not included in the
  previous release).

Version 0.3
~~~~~~~~~~~

Released on 2013-03-04.

- Fix packaging issues.
- New setting ``index_in_url`` to optionally add `index.html` to the URLs.
- New setting ``links`` to specify a list of links.
- Use EXIF info to fix orientation.
- Replace the ``jpg_quality`` setting with a dict of options.
- Manage directories with only sub-directories and add some checks.
- Change the command-line interface to use sub-commands: ``init``, ``build``
  and ``serve``.
- Parallel processing.

Version 0.2
~~~~~~~~~~~

Released on 2012-12-20.

- Improve the bundled themes (update galleria, new colorbox theme).
- Improve the CLI (new arguments, nicer output).
- Change the licence to MIT.
- Change the description file to a markdown syntax file.
- Change the settings file to a python file, and add more settings.

Version 0.1
~~~~~~~~~~~

Released on 2012-05-13.

First public release.
