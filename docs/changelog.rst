===========
 Changelog
===========

Version 2.1.dev
~~~~~~~~~~~~~~~

Released on 2019-xx-xx.

- Add setting to use relative symbolic links [:issue:`359`].
- Feeds: fix links to gallery and image [:issue:`361`].
- Add new plugin to allow one to disable ZIP generation on a per album basis
  with a ``.nozip_gallery`` file [:issue:`368`].
- Add a quiet flag [:issue:`376`].
- Make sure that read-only files can be copied [:issue:`375`].
- Update photoswipe to v4.1.3

Version 2.0
~~~~~~~~~~~

Released on 2019-01-26.

Sigal now requires Python 3.5+.

- Add some transparency for galleria's info box [:issue:`308`].
- Galleria theme now reads image data from json [:issue:`312`].
- Galleria: Load first image earlier [:issue:`307`].
- Galleria: Do not load tiles by default.
- Fixed crash when IPTC reading fails [:issue:`316`].
- Force loading of truncated files [:issue:`320`].
- Include tests in PyPI tarball [:issue:`323`].
- Optimize a bit markdown initialization [:issue:`329`].
- Quote special characters in urls [:issue:`345`].
- Reorganization of templates, splitting landing page and album templates
  [:issue:`343`], [:issue:`347`], [:issue:`348`].
- Add IPTC Headline (2:105) and to iptc_data [:issue:`356`].
- Avoid IPTC errors [:issue:`355`], [:issue:`358`].

Version 1.4.1
~~~~~~~~~~~~~

Released on 2018-10-01.

- compatibility with Click 7.0

Version 1.4.0
~~~~~~~~~~~~~

Released on 2018-02-20.

This is the last version supporting Python 2.

- Update libraries used in themes (Galleria, Colorbox, PhotoSwipe) and their
  dependencies.
- Remove use of CDNs (JQuery, Google fonts).
- Hint to how to suppress decompressionbomb warnings [:issue:`235`].
- New plugin for finer control over ignored files [:issue:`233`].
- New plugin to cache the exif data of images [:issue:`236`].
- Feeds plugin: include videos in feeds [:issue:`238`].
- Allow formatting in ``zip_gallery`` [:issue:`244`].
- Added random thumbnail property for album [:issue:`241`].
- Improve CSP compatibility with colorbox theme [:issue:`245`].
- Set html lang attribute based upon locale [:issue:`257`].
- Resize portrait images to same size as landscape [:issue:`258`].
- New setting ``thumb_fit_centering`` for tweaking how thumbnails should be
  cropped [:issue:`263`].
- New settings to configure what file extensions should be recognised as
  images and videos [:issue:`270`].
- New setting ``datetime_format`` to customize the EXIF datetime format
  [:issue:`271`].
- Add a progress bar for writing index files [:issue:`234`].
- Add setting to customize the EXIF datetime format [:issue:`271`].
- Allow to configure the ffmpeg binary [:issue:`273`].
- Filter .nomedia files with the source filename [:issue:`295`].
- Populate title & description from IPTC image data [:issue:`297`].
- Defer loading of leaflet js til late in the page [:issue:`298`].
- Add compress_assets plugin [:issue:`300`].
- Sidebar site logo image in Colorbox [:issue:`292`].

Version 1.3.0
~~~~~~~~~~~~~

Released on 2017-01-03.

- Support videos with rotation [:issue:`210`].
- Generate missing thumbnails from the resized image if possible [:issue:`211`].
- Fix background-image url in the PhotoSwipe theme [:issue:`213`].
- Implement a first version of video support for the PhotoSwipe theme [:issue:`216`].
- Update Google Analytics UA Code [:issue:`221`].
- Use leaflet-providers.js to allow chosing the tile provider for the map in
  the Galleria theme [:issue:`218`].
- Fix theme.url path in the media page plugin for the Colorbox theme. [:issue:`224`]
- Add 3gp to the list of supported video formats. [:issue:`226`]

Version 1.2.0
~~~~~~~~~~~~~

Released on 2016-06-05.

- Fix videos not opening correctly with colorbox [:issue:`201`].
- Allow to create large zip files [:issue:`205`].
- Allow sorting on metadata keys (for ``albums_sort_attr`` and
  ``medias_sort_attr``) [:issue:`202`].
- Add a ``set_meta`` command to write metadata keys to ``.md`` files [:issue:`203`]. For
  example, to set the title of ``test.jpg`` to *"My test image"*::

    sigal set_meta test.jpg title "My test image"

Version 1.1.0
~~~~~~~~~~~~~

Released on 2016-04-24.

- Add GIF support [:issue:`185`].
- Add a feeds plugin [:issue:`98`].
- Implement album sorting [:issue:`192`].
- Enable autoescape in Jinja templates [:issue:`195`].
- Raise exceptions in debug mode (``--debug``).
- Fix unicode bug with special characters in path names.
- Better representation for exposure time fraction  [:issue:`187`].
- Catch ``cPickle.PicklingError`` on python 2 [:issue:`191`].
- Fix ``ZeroDivisionError`` when ExposureTime contains null values [:issue:`193`].
- Fix hard-coded video mime-type in the galleria theme [:issue:`196`].
- Update theme libraries: colorbox 1.6.3, jQuery 2.2.1, touchSwipe 1.6.15,
  photoswipe 4.1.1
- Galleria: always show fullscreen icon, replace fullscreen and map icons.
- Use https for external resources, remove html5shiv.

Version 1.0.1
~~~~~~~~~~~~~

Released on 2015-11-19.

- Simplify a bit photoswipe's style [:issue:`181`].
- Improves CSP compatibility (Remove an inline javascript line) [:issue:`179`].
- Warn that Pillow 3.0 is broken [:issue:`184`].

Version 1.0.0
~~~~~~~~~~~~~

Released on 2015-09-07.

- Colorbox: Use the media title if available (fix #145).
- Adds a thumb_video_delay parameter for the creation of thumbnails with fade-in
  videos [:issue:`143`].
- Add fullscreen display support to Galleria theme [:issue:`149`].
- Add watermark plugin [:issue:`148`].
- Allow more settings for font, color, position in the copyright plugin [:issue:`150`].
- Tables support in markdown [:issue:`155`].
- Honor 'use_orig' for videos [:issue:`153`].
- Fix for the relative path checks for Windows [:issue:`160`].
- Add support for mp4 [:issue:`159`].
- Add size property into Image object [:issue:`164`].
- Make sure that bad exif data does not crash sigal.
- Strip spaces for some exif tags (fix #154).
- Add support for piwik [:issue:`165`].
- Add a theme using photoswipe [:issue:`163`].
- Add a setting to disable google fonts and jquery [:issue:`168`].
- Add swipe to colorbox theme [:issue:`116`].
- Map view for albums in galleria theme [:issue:`45`].

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

- New plugin which adds the ability to generate media pages [:issue:`126`].
- Decrease logs level for the parsing of exif tags [:issue:`127`].
- Enhance documentation for album information [:issue:`123`].
- Fix the title which was not unicode when using the settings file [:issue:`104`].
- Add more info on how the report a bug or contribute [:issue:`128`].
- Add more commands to the Makefile.
- Add `coveralls.io <https://coveralls.io/r/saimn/sigal?branch=master>`_
- New plugin to upload generated gallery to Amazon S3 [:issue:`114`].
- Handling of empty markdown or missing meta-data [:issue:`120`].
- Include plugins in the distributed package [:issue:`117`].
- Allow to use directly original files [:issue:`118`].
- Add settings to give a different output filename than index.html [:issue:`115`].
- Remove files that can't be processed for some reason [:issue:`112`].
- Skip files that don't exist in the ZIP archiving [:issue:`110`].
- Show progress (spinners & bars), read exif only on access [:issue:`109`].
- Use the correct filename for original videos [:issue:`111`].
- Check that the file exists before removing. [:issue:`110`].
- Enhance the ``serve`` command [:issue:`107`].
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
  ``albums_sort_reverse``, ``medias_sort_attr``, ``medias_sort_reverse`` [:issue:`2`].
- New setting (``autorotate_images``) to disable autorotation of images, and
  warn about the incompatibility between autorotation and EXIF copy [:issue:`72`].
- New settings to filter directories and files with pattern matching
  (``ignore_directories`` and ``ignore_files``) [:issue:`63`].
- New setting to customize the column width of the colorbox theme
  (``colorbox_column_size``).
- New setting to choose the media format used for ZIP archives
  (``zip_media_format``).
- Update galleria to 1.3.5 and add the history plugin [:issue:`93`].
- Skip image instead of failing when the image is corrupted [:issue:`69`].
- Better handling of album urls (quoting special caracters).

Version 0.6.0
~~~~~~~~~~~~~

Released on 2014-01-25.

- Add support for Python 3.3.
- Parallel processing (new command-line option ``-n|--ncpu``, uses all cores by
  default).
- Adding keyboard shortcuts for the galleria theme [#32, #39].
- Include symlinked directories in the source directory.
- New setting to use symbolic links for original files (``orig_link``) [:issue:`36`].
- New setting for the video size (``video_size``) [:issue:`35`].
- Add a colored formatter for verbose and debug modes.
- ``webm_options`` is now a list with ffmpeg options, to allow better
  flexibility and compatibility with avconv.
- New setting to copy files from the source directory to the destination
  (``files_to_copy``).

Bugfixes:

- Avoid issues with corrupted exif data.
- Fix exif data not read from .JPEG files [:issue:`58`].
- Fix whitespace issues with video filenames [:issue:`54`].

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
- Move unit tests to pytest.
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
