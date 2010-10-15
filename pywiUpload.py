#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pywiUpload - Piwigo gallery generator
# Copyright (C) 2009 saimon.org
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

"""Prepare a gallery of images for Piwigo

This script resize images, create thumbnails with some options
(rename images, squared thumbs, ...), and upload images to a FTP server.
"""

__author__ = "Saimon (contact at saimon.org)"
__version__ = "0.7"
__date__ = "20090628"
__copyright__ = "Copyright (c) 2009 saimon.org"
__license__ = "GPL"

import os,sys
import getpass
import Image,ImageDraw
from ftplib import FTP
from configobj import ConfigObj

class pywiUpload:
    "Prepare a gallery of images for Piwigo"

    def __init__(self, conf=None):
        self.filepath = ""
        self.galname = ""
        self.params = {}
        configFile = conf if conf \
                        else os.path.join(sys.path[0], 'pywiUpload.conf')
        self.readParams(configFile)

    def getPath(self, pathname):
        "return abslolute path from params dict"
        return os.path.join(self.filepath, self.params[pathname]) \
                if self.params.has_key(pathname) else ""

    def createGallery(self, path):
        "create image gallery"
        imgFileList = self.listFilesInDir(path)
        print "Found %i images in %s" % (len(imgFileList), path)

        while self.galname == "":
            self.galname = raw_input('Enter gallery name: ')

        self.filepath = os.path.join(os.path.dirname(imgFileList[0]),
                                                     self.galname)

        print "Create output dir ..."
        try:
            os.makedirs(self.getPath('thumb_dir'))
        except OSError:
            pass

        if self.params['bigimg']:
            try:
                os.mkdir(self.getPath('bigimg_dir'))
            except OSError:
                pass

        outFileList = self.processImages(imgFileList)

        upload = raw_input("Upload images to your FTP server ? (y/[n]) ")
        if upload == 'y':
            self.ftpUpload(outFileList)

    def processImages(self,imgFileList):
        "prepare images"
        imgFileList.sort()
        outImgList = []
        outThumbList = []
        outBigImgList = []

        renImg = raw_input("Rename images ('name01.jpg') ? (y/[n]) ")
        if renImg == 'y':
            count = 1
            imgname = raw_input('Enter new image name: ')
            nfill = 2 if (len(imgFileList)<100) else 3

        if self.params['copyright']:
            copyrightmsg = raw_input('Enter copyright message: ')
            copyrightmsg = '\xa9 ' + copyrightmsg

        # loop on images
        for f in imgFileList:
            filename = os.path.split(f)[1]
            im = Image.open(f)

            if renImg == 'y':
                filename = imgname+str(count).zfill(nfill)+'.jpg'
                print "%s > %s" % (os.path.split(f)[1],filename)
                count += 1
            else:
                print "%s" % filename

            if self.params['bigimg']:
                im.save(os.path.join(self.getPath('bigimg_dir'),filename),
                        quality=self.params['jpgquality'])
                outBigImgList.append(os.path.join(self.getPath('bigimg_dir'),
                                                  filename))

            # resize image
            if im.size[0] > im.size[1]:
                im_size = (self.params['im_width'],self.params['im_height'])
            else:
                im_size = (self.params['im_height'],self.params['im_width'])
            im2 = im.resize(im_size,Image.ANTIALIAS)

            # create thumbnail
            if self.params['squarethumb']:
                if im.size[0] > im.size[1]:
                    offset = (im.size[0] - im.size[1])/2
                    box = (offset,0,im.size[0]-offset,im.size[1])
                else:
                    offset = (im.size[1] - im.size[0])/2
                    box = (0,offset,im.size[0],im.size[1]-offset)

                im = im.crop(box)
                thumbsize = (self.params['thumb_width'],self.params['thumb_width'])
            else:
                thumbsize = (self.params['thumb_width'],self.params['thumb_height'])

            im.thumbnail(thumbsize,Image.ANTIALIAS)

            # copyright
            if self.params['copyright']:
                draw=ImageDraw.Draw(im2)
                draw.text((5,im2.size[1]-15),copyrightmsg)

            # save
            im.save(os.path.join(self.getPath('thumb_dir'),
                                 self.params['thumb_prefix']+filename),
                    quality=self.params['jpgquality'])
            im2.save(os.path.join(self.filepath,filename),
                     quality=self.params['jpgquality'])

            outThumbList.append(os.path.join(self.getPath('thumb_dir'),
                                             self.params['thumb_prefix']+filename))
            outImgList.append(os.path.join(self.filepath,filename))

            # exif metadatas
            if self.params['exif']:
                self.processExif(f, os.path.join(self.filepath,filename))

        return [outImgList,outThumbList,outBigImgList]

    def processExif(self, srcfile, dstfile):
        "copy exif metadatas from src to dest images"
        if self.params['exif']:
            try:
                import pyexiv2
            except ImportError:
                self.params['exif']=0
                print "Error: install pyexiv2 module to use exif metadatas."
                return

        if pyexiv2.version_info[1] == 1:
            src = pyexiv2.Image(srcfile)
            dst = pyexiv2.Image(dstfile)
            src.readMetadata()
            dst.readMetadata()
            try:
                src.copyMetadataTo(dst)
            except:
                print "Error: metadata not copied for %s." % srcfile
                return
            dst.writeMetadata()
        else:
            src = pyexiv2.ImageMetadata(srcfile)
            dst = pyexiv2.ImageMetadata(dstfile)
            src.read()
            dst.read()
            try:
                src.copy(dst)
            except:
                print "Error: metadata not copied for %s." % srcfile
                return
            dst.write()


    def ftpUpload(self,imgFileList):
        "Upload images to a FTP server"
        print "Connect to %s ..." % self.params['host']
        try:
            password = getpass.getpass()
            ftp = FTP(self.params['host'],self.params['user'],password)
        except:
            print "FTP connexion error, abort."
            return
        print "Connected !"

        try:
            ftp.cwd(self.params['piwigo_dir'])
            ftp.cwd('galleries')
        except:
            print "Error: wrong 'galleries' path"

        print "\nChoose the category in which your gallery will be uploaded:"
        print "- enter a number to go in a sub-category"
        print "- choose '.' for uploading in the current directory"

        # choose upload dir
        while 1:
            i = 1
            ftpdir = [f for f in ftp.nlst()
                        if f not in self.params['fileExclude']]
            print "\n"
            for dir in ftpdir:
                print "%i: %s" % (i,dir)
                i += 1

            try:
                choice = int(raw_input("Enter directory number: ")) - 1
                if ftpdir[choice] == '.': break
                ftp.cwd(ftpdir[choice])
            except:
                print "Error: invalid choice"

        print "Upload files to %s directory:" % self.galname
        try:
            ftp.mkd(self.galname)
        except:
            choice = raw_input("Directory exist, continue ? (y/[n]) ")
            if choice != 'y':
                ftp.close()
                return

        # upload images
        ftp.cwd(self.galname)
        self.fileUpload(ftp,imgFileList[0])

        # upload thumbnails
        try:
            ftp.mkd(self.params['thumb_dir'])
        except:
            pass
        ftp.cwd(self.params['thumb_dir'])
        self.fileUpload(ftp,imgFileList[1])

        # upload big images
        if self.params['bigimg']:
            ftp.cwd('..')
            try:
                ftp.mkd(self.params['bigimg_dir'])
            except:
                pass
            ftp.cwd(self.params['bigimg_dir'])
            self.fileUpload(ftp,imgFileList[2])

        # close FTP connection
        ftp.quit()

    def fileUpload(self,ftp,imgFileList):
        "Upload list of files in the current working directory of ftp"
        for f in imgFileList:
            print "Upload %s ..." % os.path.basename(f)
            file = open(f, 'rb')
            try:
                ftp.storbinary('STOR '+os.path.basename(f), file)
            except:
                print "Tranfer error !"
            file.close()

    def listFilesInDir(self, directory):
        "get list of files of particular extensions"
        fileList = [os.path.normcase(f) for f in os.listdir(directory)]
        return [os.path.join(directory, f) for f in fileList \
                    if os.path.splitext(f)[1] in self.params['fileExtList']]

    def readParams(self,configFile):
        "Read params from a config file"
        try:
            print "Reading parameters ..."
            self.params = ConfigObj(configFile,file_error=True)
        except:
            sys.exit("Config file not found, exiting ...")

        # convert types
        self.params["im_width"] = int(self.params["im_width"])
        self.params["im_height"] = int(self.params["im_height"])
        self.params["thumb_width"] = int(self.params["thumb_width"])
        self.params["thumb_height"] = int(self.params["thumb_height"])
        self.params["bigimg"] = int(self.params["bigimg"])
        self.params["squarethumb"] = int(self.params["squarethumb"])
        self.params["jpgquality"] = int(self.params["jpgquality"])
        self.params["exif"] = int(self.params["exif"])
        self.params["copyright"] = int(self.params["copyright"])

if __name__ == "__main__":
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    version="version %s, %s" % (__version__, __date__)
    parser = OptionParser(usage=usage, version="%prog "+version)

    parser.add_option("-c", "--config", dest="config",
                      help="specify an alternative config file")
    parser.add_option("-i", "--imgpath", dest="imgpath",
                      help="specify images path")

    (options, args) = parser.parse_args()

    if options.config:
        gallery = pywiUpload(conf=options.config)
    else:
        gallery = pywiUpload()

    if options.imgpath:
        path = options.imgpath
    else:
        path = os.getcwd()

    gallery.createGallery(path)

    print "Finished !\n"
