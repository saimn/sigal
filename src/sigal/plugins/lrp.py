"""Plugin which add raw support.

Plugin make temp directory which is use for generate jpeg from raw file (jpeg is camera-generated thumbnail).
For this dcraw program is used.

"""

import logging

from sigal import signals

import os
import sys
import re

from ..gallery import Image
from ..settings import Status, get_thumb
import copy

logger = logging.getLogger(__name__)

tempDir="/tmp/rawTempSigal"

def pouTest(gallery):

	if gallery.src_ext == '.orf':
		logger.info('Processing RAW: '+gallery.dst_filename)
		newFilename=re.sub('ORF', 'jpeg', gallery.dst_filename)
		tmpname = tempDir + '/'+newFilename

		os.system('dcraw -c -e "' + gallery.src_path + '" > "' + tmpname + '"')
		
		gallery.src_path=tmpname
		gallery.basename = os.path.splitext(newFilename)[0]
		gallery.dst_filename = newFilename
		gallery.src_filename = newFilename
		gallery.src_ext = os.path.splitext(newFilename)[1].lower()
		gallery.src_path = tmpname
		gallery.thumb_name = get_thumb(gallery.settings, gallery.dst_filename)


def register(settings):
    logger.info('INIT lite raw plugin')
    os.system("rm -rf "+tempDir)
    os.makedirs(tempDir)
    signals.media_initialized.connect(pouTest)
    
