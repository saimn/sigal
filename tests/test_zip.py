import glob
import os
import zipfile

from sigal import init_plugins
from sigal.gallery import Gallery
from sigal.settings import read_settings

CURRENT_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(CURRENT_DIR, 'sample')
SAMPLE_SOURCE = os.path.join(SAMPLE_DIR, 'pictures')


def make_gallery(source_dir='dir1', **kwargs):
    default_conf = os.path.join(SAMPLE_DIR, 'sigal.conf.py')
    settings = read_settings(default_conf)
    settings['source'] = os.path.join(SAMPLE_SOURCE, source_dir)
    settings.update(kwargs)
    init_plugins(settings)
    return Gallery(settings, ncpu=1)


def test_zipped_correctly(tmpdir):
    outpath = str(tmpdir)
    gallery = make_gallery(destination=outpath, zip_gallery='archive.zip')
    gallery.build()

    zipf = os.path.join(outpath, 'test1', 'archive.zip')
    assert os.path.isfile(zipf)

    zip_file = zipfile.ZipFile(zipf, 'r')
    expected = ('11.jpg', 'CMB_Timeline300_no_WMAP.jpg',
                'flickr_jerquiaga_2394751088_cc-by-nc.jpg',
                'example.gif')

    for filename in zip_file.namelist():
        assert filename in expected

    zip_file.close()

    assert os.path.isfile(os.path.join(outpath, 'test2', 'archive.zip'))


def test_not_zipped(tmpdir):
    # test that the zip file is not created when the .nozip_gallery file
    # is present
    outpath = str(tmpdir)
    gallery = make_gallery(destination=outpath, zip_gallery='archive.zip',
                           source_dir='dir2')
    gallery.build()
    assert not os.path.isfile(os.path.join(outpath, 'archive.zip'))


def test_no_archive(tmpdir):
    outpath = str(tmpdir)
    gallery = make_gallery(destination=outpath, zip_gallery=False)
    gallery.build()

    assert not os.path.isfile(os.path.join(outpath, 'test1', 'archive.zip'))
    assert not os.path.isfile(os.path.join(outpath, 'test2', 'archive.zip'))
