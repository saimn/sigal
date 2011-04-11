#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - Piwigo gallery generator
# Copyright (C) 2009-2011 - saimon.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; If not, see http://www.gnu.org/licenses/

"""Prepare and upload a gallery of images for Piwigo

This script resize images, create thumbnails with some options
(rename images, squared thumbs, ...), and upload images to a FTP server.
"""

__author__ = "Saimon (contact at saimon dot org)"
__version__ = "0.8"
__date__ = "20100722"
__copyright__ = "Copyright (C) 2009 - saimon.org"
__license__ = "GPL"

import os
import sys
from optparse import OptionParser
from sigal.ftp import FtpUpload
from sigal.image import Gallery
from sigal.params import read_params

def main():
    "main program"

    # command line options
    usage = "usage: %prog [options] inputdir outputdir"
    version = "version %s, %s" % (__version__, __date__)

    parser = OptionParser(usage=usage, version="%prog "+version)

    parser.add_option("-c", "--config", dest="config",
                      help="specify an alternative config file")
    parser.add_option("-f", "--ftp-upload", dest="ftp_upload",
                      help="upload file using ftp")

    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.print_help()
        sys.exit()

    input_dir = args[0]
    output_dir = args[1]

    if not os.path.isdir(input_dir):
        print "Directory %s does not exist." % input_dir
        sys.exit(1)

    if not os.path.isdir(output_dir):
        print "Create %s" % output_dir
        os.makedirs(output_dir)

    # read params from config file
    config_file = options.config if options.config \
                  else os.path.join(sys.path[0], 'sigal.conf')

    print "Reading parameters ..."
    params = read_params(config_file)

    # create gallery
    gallery = Gallery(params)
    out_filelist = gallery.create_gallery(input_dir, output_dir)

    # upload
    if options.ftp_upload:
        galleryname = raw_input("Enter directory name :")
        ftp = FtpUpload(params["host"], params["user"], \
                        params["piwigo_dir"] + '/galleries')
        if params["bigimg"]:
            ftp.upload(out_filelist, galleryname, params["thumb_dir"],
                        params["bigimg_dir"])
        else:
            ftp.upload(out_filelist, galleryname, params["thumb_dir"])
        ftp.close()

    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
