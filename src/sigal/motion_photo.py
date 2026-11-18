# Copyright (c) 2009-2026 - Simon Conseil
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import logging
import os
import re
import struct

logger = logging.getLogger(__name__)

# Valid image extensions that can contain embedded motion photos
MOTION_PHOTO_IMAGE_EXTS = {".jpg", ".jpeg", ".heic", ".webp"}

# Patterns for Google Camera Motion Photo / MicroVideo metadata
RE_MICRO_VIDEO_OFFSET = re.compile(
    rb"""(?:MicroVideoOffset[\"\\\x27:=\s]+(\d+)|<GCamera:MicroVideoOffset>(\d+)</GCamera:MicroVideoOffset>)""",
    re.IGNORECASE,
)
RE_CONTAINER_LENGTH = re.compile(
    rb"""(?:Item:Length[\"\\\x27:=\s]+(\d+)|<Item:Length>(\d+)</Item:Length>)""",
    re.IGNORECASE,
)
RE_MOTION_PHOTO_MARKER = re.compile(
    rb"""(?:GCamera:MotionPhoto[\"\\\x27:=\s]+1|Camera:MotionPhoto[\"\\\x27:=\s]+1|GCamera:MicroVideo[\"\\\x27:=\s]+1|Item:Semantic[\"\\\x27:=\s]+MotionPhoto|<Item:Semantic>MotionPhoto</Item:Semantic>)""",
    re.IGNORECASE,
)


def is_motion_photo_file(file_path):
    """Determine if a file is a motion photo containing an embedded video.

    Checks for:
    1. Google Camera Motion Photo (XMP Container / MicroVideo)
    2. Samsung Motion Photo (MotionPhoto_Data marker / SEFH)
    3. Appended MP4 video after JPEG EOI marker

    :param file_path: Path to the image file
    :return: True if the file contains an embedded motion photo video, False otherwise
    """
    if not os.path.isfile(file_path):
        return False

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in MOTION_PHOTO_IMAGE_EXTS:
        return False

    try:
        file_size = os.path.getsize(file_path)
    except OSError:
        return False

    if file_size < 64:
        return False

    # Read the beginning of the file (first 512KB for XMP metadata)
    read_size = min(file_size, 512 * 1024)
    with open(file_path, "rb") as f:
        header = f.read(read_size)

    # Check for Google Camera Motion Photo markers in header
    if RE_MOTION_PHOTO_MARKER.search(header):
        return True

    if RE_MICRO_VIDEO_OFFSET.search(header):
        return True

    # Read the end of the file (last 512KB for Samsung markers / trailers)
    tail_read = min(file_size, 512 * 1024)
    with open(file_path, "rb") as f:
        f.seek(file_size - tail_read)
        tail = f.read(tail_read)

    if b"MotionPhoto_Data" in tail or b"MotionPhoto" in tail:
        return True

    # Check if get_motion_video_offset finds a valid embedded MP4
    offset_info = get_motion_video_offset(file_path)
    return offset_info is not None


def get_motion_video_offset(file_path):
    """Find the byte offset and length of an embedded video within an image file.

    :param file_path: Path to the image file
    :return: (video_start_offset, video_length) or None if not found
    """
    if not os.path.isfile(file_path):
        return None

    try:
        file_size = os.path.getsize(file_path)
    except OSError:
        return None

    if file_size < 64:
        return None

    # Step 1: Check header for XMP metadata with offset/length
    read_size = min(file_size, 512 * 1024)
    with open(file_path, "rb") as f:
        header = f.read(read_size)

    # Check MicroVideoOffset
    m_micro = RE_MICRO_VIDEO_OFFSET.search(header)
    if m_micro:
        for g in m_micro.groups():
            if g:
                offset = int(g)
                start = file_size - offset
                if 0 <= start < file_size - 8:
                    # Validate MP4 ftyp box at start
                    with open(file_path, "rb") as f:
                        f.seek(start)
                        check_bytes = f.read(16)
                    if len(check_bytes) >= 8 and check_bytes[4:8] == b"ftyp":
                        return start, offset

    # Check Container Item:Length
    m_len = RE_CONTAINER_LENGTH.search(header)
    if m_len:
        for g in m_len.groups():
            if g:
                length = int(g)
                start = file_size - length
                if 0 <= start < file_size - 8:
                    with open(file_path, "rb") as f:
                        f.seek(start)
                        check_bytes = f.read(16)
                    if len(check_bytes) >= 8 and check_bytes[4:8] == b"ftyp":
                        return start, length

    # Step 2: Check for Samsung MotionPhoto_Data marker
    # Often located towards the end of the file
    tail_size = min(file_size, 1024 * 1024)
    with open(file_path, "rb") as f:
        f.seek(file_size - tail_size)
        tail = f.read(tail_size)

    pos = tail.rfind(b"MotionPhoto_Data")
    if pos != -1:
        # Look for ftyp within 128 bytes after marker
        ftyp_rel = tail.find(b"ftyp", pos, min(len(tail), pos + 128))
        if ftyp_rel != -1:
            start_in_tail = ftyp_rel - 4
            start = (file_size - tail_size) + start_in_tail
            length = file_size - start
            return start, length

    # Step 3: Check after JPEG EOI marker (\xFF\xD9)
    # Read the file to locate JPEG EOI and subsequent ftyp
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        # JPEG files end the still image with \xFF\xD9
        # In a motion photo, the MP4 is appended after this marker.
        with open(file_path, "rb") as f:
            content = f.read()

        eoi_pos = content.find(b"\xff\xd9")
        if eoi_pos != -1 and eoi_pos < file_size - 16:
            ftyp_pos = content.find(b"ftyp", eoi_pos)
            if ftyp_pos != -1:
                start = ftyp_pos - 4
                if 0 <= start < file_size - 8:
                    box_size = struct.unpack(">I", content[start : start + 4])[0]
                    if 8 <= box_size <= 1024:
                        return start, file_size - start

    return None


def extract_motion_video(src_path, dst_path, force=False):
    """Extract the embedded MP4 video from an image file into dst_path.

    :param src_path: Path to the source motion photo image
    :param dst_path: Path to the target MP4 video file
    :param force: If True, overwrite existing destination file
    :return: True if video was successfully extracted, False otherwise
    """
    if os.path.isfile(dst_path) and not force and os.path.getsize(dst_path) > 0:
        return True

    offset_info = get_motion_video_offset(src_path)
    if not offset_info:
        logger.debug("No embedded motion video found in %s", src_path)
        return False

    video_start, video_length = offset_info
    logger.info(
        "Extracting motion photo video from %s (%d bytes at offset %d) to %s",
        src_path,
        video_length,
        video_start,
        dst_path,
    )

    dst_dir = os.path.dirname(dst_path)
    if dst_dir and not os.path.exists(dst_dir):
        os.makedirs(dst_dir, exist_ok=True)

    try:
        with open(src_path, "rb") as f_in:
            f_in.seek(video_start)
            with open(dst_path, "wb") as f_out:
                remaining = video_length
                while remaining > 0:
                    chunk_size = min(65536, remaining)
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    remaining -= len(chunk)

        if os.path.isfile(dst_path) and os.path.getsize(dst_path) > 0:
            return True
        else:
            logger.warning("Extracted motion video is empty: %s", dst_path)
            if os.path.isfile(dst_path):
                os.remove(dst_path)
            return False
    except Exception as e:
        logger.error("Failed to extract motion video from %s: %s", src_path, e)
        if os.path.isfile(dst_path):
            try:
                os.remove(dst_path)
            except OSError:
                pass
        return False


def find_paired_motion_video(img_path):
    """Check if there is a separate video file in the same directory that pairs

    with this image (e.g. Apple Live Photo or manual pair).
    """
    base, _ = os.path.splitext(img_path)
    candidates = [
        base + ".mp4",
        base + ".MP4",
        base + ".mov",
        base + ".MOV",
        base + "_motion.mp4",
        base + ".motion.mp4",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None
