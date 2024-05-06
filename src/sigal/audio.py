# Copyright (c)      2013 - Christophe-Marie Duquesne
# Copyright (c) 2013-2023 - Simon Conseil
# Copyright (c)      2021 - Keith Feldman

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from os.path import dirname, join

from . import utils
from .utils import is_valid_html5_audio

AUDIO_THUMB_FILE = join(dirname(__file__), "audio_file.png")


def process_audio(media):
    """Process an audio file: create thumbnail."""
    settings = media.settings

    with utils.raise_if_debug() as status:
        utils.copy(media.src_path, media.dst_path, symlink=settings["orig_link"])

    if settings["make_thumbs"]:
        utils.copy(AUDIO_THUMB_FILE, media.thumb_path)

    return status.value
