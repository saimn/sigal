===========
 Changelog
===========

Version 1.1.0
~~~~~~~~~~~~~

Released on 2015-xx-xx.

Nothing yet.

Version 1.0.0
~~~~~~~~~~~~~

Released on 2015-09-07.

- Colorbox: Use the media title if available (fix #145).
- Adds a thumb_video_delay parameter for the creation of thumbnails with fade-in
  videos [#143].
- Add fullscreen display support to Galleria theme [#149].
- Add watermark plugin [#148].
- Allow more settings for font, color, position in the copyright plugin [#150].
- Tables support in markdown [#155].
- Honor 'use_orig' for videos [#153].
- Fix for the relative path checks for Windows [#160].
- Add support for mp4 [#159].
- Add size property into Image object [#164].
- Make sure that bad exif data does not crash sigal.
- Strip spaces for some exif tags (fix #154).
- Add support for piwik [#165].
- Add a theme using photoswipe [#163].
- Add a setting to disable google fonts and jquery [#168].
- Add swipe to colorbox theme [#116].
- Map view for albums in galleria theme [#45].

Version 0.9.2
~~~~~~~~~~~~~

Released on 2015-01-25.

- Allow to specify the author of an album (ref #139).
- Fix encoding issue with the progress bar on py3 (fix #137).
- Avoid failure when an image can't be read (fix #134).

Version 0.9.1
~~~~~~~~~~~~~

Released on 2014-12-08.

- Fix images path for the galleria theme (fix #130).

Version 0.9.0
~~~~~~~~~~~~~

Released on 2014-12-07.

- New plugin which adds the ability to generate media pages [#126].
- Decrease logs level for the parsing of exif tags [#127].
- Enhance documentation for album information [#123].
- Fix the title which was not unicode when using the settings file [#104].
- Add more info on how the report a bug or contribute [#128].
- Add more commands to the Makefile.
- Add `coveralls.io <https://coveralls.io/r/saimn/sigal?branch=master>`_
- New plugin to upload generated gallery to Amazon S3 [#114].
- Handling of empty markdown or missing meta-data [#120].
- Include plugins in the distributed package [#117].
- Allow to use directly original files [#118].
- Add settings to give a different output filename than index.html [#115].
- Remove files that can't be processed for some reason [#112].
- Skip files that don't exist in the ZIP archiving [#110].
- Show progress (spinners & bars), read exif only on access [#109].
- Use the correct filename for original videos [#111].
- Check that the file exists before removing. [#110].
- Enhance the ``serve`` command [#107].
- Catch cPickle error and add a message about serialization error with the
  settings file.

Version 0.8.1
~~~~~~~~~~~~~

Released on 2014-10-07.

- Include plugins in the distributed package.

Version 0.8.0
~~~~~~~~~~~~~

Released on 2014-08-30.

- Add a setting and a cli option to specify the gallery title (``title`` and
  ``--title``) (ref #91).
- Add a mailing list at Librelist (sigal at librelist.com).
- Add an option to specify the port to use for the serve command.
- Replace argh with click.
- Don't overwrite existing config file (with the init command).
- Don't fail if there are no pictures.
- Use plain css to simplify theme customizing (no more sass).
- Upgrade colorbox 1.5.13
- Upgrade galleria 1.4.2
- Use HTML5 output for Markdown.
- Allow to read additional data for images from markdown files.
- Use case insensitive check for file extensions (fix #99).
- Add a plugin system with blinker, and make plugins for copyright and adjust.
- Mention the irc channel on freenode and add travis notifications.
- Avoid failure if GPS tags contain zero values (fix #96).
- Remove output file when the ffmpeg process has been interrupted (ref #90).
- Fix thumbnail urls to always use slashes (ref #81).

Version 0.7
~~~~~~~~~~~

Released on 2014-05-10.

- Refactor the way to store album and media informations. Albums, images and
  videos are now represented by objects, and these objects are directly
  available in the templates. The following template variables have been
  renamed:

  - ``albums`` => ``album.albums``
  - ``breadcrumb`` => ``album.breadcrumb``
  - ``description`` => ``album.description``
  - ``index_url`` => ``album.index_url``
  - ``medias`` => ``album.medias``
  - ``title`` => ``album.title``
  - ``media.file`` => ``media.filename``
  - ``media.thumb`` => ``media.thumbnail``
  - ``zip_gallery`` => ``album.zip``

- New settings to define the sort order for albums and medias:
  ``albums_sort_reverse``, ``medias_sort_attr``, ``medias_sort_reverse`` [#2].
- New setting (``autorotate_images``) to disable autorotation of images, and
  warn about the incompatibility between autorotation and EXIF copy [#72].
- New settings to filter directories and files with pattern matching
  (``ignore_directories`` and ``ignore_files``) [#63].
- New setting to customize the column width of the colorbox theme
  (``colorbox_column_size``).
- New setting to choose the media format used for ZIP archives
  (``zip_media_format``).
- Update galleria to 1.3.5 and add the history plugin [#93].
- Skip image instead of failing when the image is corrupted [#69].
- Better handling of album urls (quoting special caracters).

Version 0.6.0
~~~~~~~~~~~~~

Released on 2014-01-25.

- Add support for Python 3.3.
- Parallel processing (new command-line option ``-n|--ncpu``, uses all cores by
  default).
- Adding keyboard shortcuts for the galleria theme [#32, #39].
- Include symlinked directories in the source directory.
- New setting to use symbolic links for original files (``orig_link``) [#36].
- New setting for the video size (``video_size``) [#35].
- Add a colored formatter for verbose and debug modes.
- ``webm_options`` is now a list with ffmpeg options, to allow better
  flexibility and compatibility with avconv.
- New setting to copy files from the source directory to the destination
  (``files_to_copy``).

Bugfixes:

- Avoid issues with corrupted exif data.
- Fix exif data not read from .JPEG files [#58].
- Fix whitespace issues with video filenames [#54].

Version 0.5.1
~~~~~~~~~~~~~

Released on 2013-09-23.

- Fix error in calculating the degrees from exif data.

Version 0.5.0
~~~~~~~~~~~~~

Released on 2013-09-06.

- Add support for videos. Videos are encoded to webm (see the ``webm_options``
  setting).
- Check jinja2's version for ``lstrip_blocks`` (only for Jinja 2.7+).
- Add option to zip galleries. See the ``zip_gallery`` setting.
- Add support for EXIF tags and GPS coordinates. EXIF tags are added to the
  media context (for themes). The ``copy_exif_data`` setting allow to choose if
  the exif data from the original image is copied to the resized image.
- Correct themes design with long directory names.
- Add the possibility to adjust images after resizing (with the Adjust
  processor from Pilkit). See the ``adjust_options`` setting.
- Add the possibility to disable image resizing.

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
