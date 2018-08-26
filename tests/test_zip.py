import os
import glob
import zipfile

from sigal.gallery import Gallery
from sigal.settings import read_settings

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')
SAMPLE_SOURCE = os.path.join(SAMPLE_DIR, 'pictures', 'dir1')


def make_gallery(**kwargs):
    default_conf = os.path.join(SAMPLE_DIR, 'sigal.conf.py')
    settings = read_settings(default_conf)
    settings['source'] = SAMPLE_SOURCE
    settings.update(kwargs)
    return Gallery(settings, ncpu=1)


def test_zipped_correctly(tmpdir):
    outpath = str(tmpdir)
    gallery = make_gallery(destination=outpath,
                           zip_gallery='archive.zip')
    gallery.build()

    zipped1 = glob.glob(os.path.join(outpath, 'test1', '*.zip'))
    assert len(zipped1) == 1
    assert os.path.basename(zipped1[0]) == 'archive.zip'

    zip_file = zipfile.ZipFile(zipped1[0], 'r')
    expected = ('11.jpg', 'archlinux-kiss-1024x640.png',
                'flickr_jerquiaga_2394751088_cc-by-nc.jpg',
                '50a1d0bc-763d-457e-b634-c87f16a64270.gif')

    for filename in zip_file.namelist():
        assert filename in expected

    zip_file.close()

    zipped2 = glob.glob(os.path.join(outpath, 'test2', '*.zip'))
    assert len(zipped2) == 1
    assert os.path.basename(zipped2[0]) == 'archive.zip'


def test_no_archive(tmpdir):
    outpath = str(tmpdir)
    gallery = make_gallery(destination=outpath,
                           zip_gallery=False)
    gallery.build()

    assert not glob.glob(os.path.join(outpath, 'test1', '*.zip'))
    assert not glob.glob(os.path.join(outpath, 'test2', '*.zip'))
