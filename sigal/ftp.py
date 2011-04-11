#! /usr/bin/env python2
# -*- coding:utf-8 -*-

# sigal - Piwigo gallery generator
# Copyright (C) 2009, 2011 - saimon.org
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

"""Upload images by FTP
"""

import os
import getpass
import ftplib

class FtpUpload:
    "Upload a list of files by FTP"

    # files excluded when listing directories' content
    FILE_EXCLUDE = ["index.php", ".cvsignore"]

    def __init__(self, host, user, basedir):
        print "Connect to %s ..." % host
        password = getpass.getpass()
        self.ftp = ftplib.FTP(host, user, password)
        self.ftp.cwd(basedir)

    # FIXME: galname
    def upload(self, imgfilelist, galname, thumb_dir, bigimg_dir=None):
        "Upload images to a FTP server"

        print "\nChoose the category in which your gallery will be uploaded:"
        print "- enter a number to go in a sub-category"
        print "- choose '.' for uploading in the current directory"

        # choose upload dir
        while 1:
            i = 1
            ftpdir = [f for f in self.ftp.nlst() if f not in self.FILE_EXCLUDE]
            print "\n"
            for ldir in ftpdir:
                print "%i: %s" % (i, ldir)
                i += 1

            try:
                choice = int(raw_input("Enter directory number: ")) - 1
                if ftpdir[choice] == '.':
                    break
                self.ftp.cwd(ftpdir[choice])
            except:
                print "Error: invalid choice"

        print "Upload files to %s directory:" % galname
        try:
            self.ftp.mkd(galname)
        except:
            choice = raw_input("Directory exist, continue ? (y/[n]) ")
            if choice != 'y':
                return

        # upload images
        self.ftp.cwd(galname)
        self.upload_files(imgfilelist[0])

        # upload thumbnails
        try:
            self.ftp.mkd(thumb_dir)
        except:
            pass
        self.ftp.cwd(thumb_dir)
        self.upload_files(imgfilelist[1])

        # upload big images
        if bigimg_dir:
            self.ftp.cwd('..')
            try:
                self.ftp.mkd(bigimg_dir)
            except:
                pass
            self.ftp.cwd(bigimg_dir)
            self.upload_files(imgfilelist[2])

    def upload_files(self, imgfilelist):
        "Upload list of files in the current working directory of ftp"
        for i in imgfilelist:
            print "Upload %s ..." % os.path.basename(i)
            ofile = open(i, 'rb')
            try:
                self.ftp.storbinary('STOR '+os.path.basename(i), ofile)
            except:
                print "Tranfer error !"
            ofile.close()

    def close(self):
        "Close FTP connection"
        self.ftp.quit()

