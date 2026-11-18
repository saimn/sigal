import io
import os
import struct
from PIL import Image as PILImage

from sigal.gallery import Gallery, Image
from sigal.motion_photo import (
    extract_motion_video,
    find_paired_motion_video,
    get_motion_video_offset,
    is_motion_photo_file,
)
from sigal.settings import create_settings


def create_dummy_mp4():
    """Create a minimal valid MP4 header and dummy payload."""
    ftyp_payload = b"mp42\x00\x00\x00\x00mp42isom"
    box_size = 8 + len(ftyp_payload)
    ftyp_box = struct.pack(">I", box_size) + b"ftyp" + ftyp_payload
    # Add dummy mdat box
    mdat_payload = b"test_video_data_12345"
    mdat_box = struct.pack(">I", 8 + len(mdat_payload)) + b"mdat" + mdat_payload
    return ftyp_box + mdat_box


def create_dummy_jpeg(extra_header=b""):
    """Create a valid JPEG image with optional embedded header."""
    buf = io.BytesIO()
    im = PILImage.new("RGB", (100, 100), color="red")
    im.save(buf, format="JPEG")
    data = buf.getvalue()
    if extra_header:
        # Insert extra header right after SOI marker (\xff\xd8)
        return data[:2] + extra_header + data[2:]
    return data


def test_google_microvideo_detection_and_extraction(tmp_path):
    """Test Google Camera MicroVideo format detection and video extraction."""
    mp4_data = create_dummy_mp4()
    offset_str = str(len(mp4_data)).encode("ascii")
    xmp_meta = b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description xmlns:GCamera="http://ns.google.com/photos/1.0/camera/" GCamera:MicroVideo="1" GCamera:MicroVideoOffset="' + offset_str + b'"/></rdf:RDF></x:xmpmeta>'
    
    jpeg_data = create_dummy_jpeg(extra_header=xmp_meta)
    photo_file = str(tmp_path / "MVIMG_test.jpg")
    with open(photo_file, "wb") as f:
        f.write(jpeg_data + mp4_data)

    # Verify detection
    assert is_motion_photo_file(photo_file) is True
    offset_info = get_motion_video_offset(photo_file)
    assert offset_info is not None
    start, length = offset_info
    assert length == len(mp4_data)
    assert start == len(jpeg_data)

    # Verify extraction
    dst_video = str(tmp_path / "extracted.mp4")
    success = extract_motion_video(photo_file, dst_video)
    assert success is True
    assert os.path.isfile(dst_video)
    with open(dst_video, "rb") as f:
        extracted = f.read()
    assert extracted == mp4_data


def test_google_container_motion_photo(tmp_path):
    """Test Google Camera Container Directory Item:Length format."""
    mp4_data = create_dummy_mp4()
    length_str = str(len(mp4_data)).encode("ascii")
    xmp_meta = b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description GCamera:MotionPhoto="1"><Container:Directory><rdf:Seq><rdf:li Item:Length="' + length_str + b'" Item:Mime="video/mp4" Item:Semantic="MotionPhoto"/></rdf:Seq></Container:Directory></rdf:Description></rdf:RDF></x:xmpmeta>'

    jpeg_data = create_dummy_jpeg(extra_header=xmp_meta)
    photo_file = str(tmp_path / "PXL_test.mp.jpg")
    with open(photo_file, "wb") as f:
        f.write(jpeg_data + mp4_data)

    assert is_motion_photo_file(photo_file) is True
    offset_info = get_motion_video_offset(photo_file)
    assert offset_info is not None
    start, length = offset_info
    assert length == len(mp4_data)

    dst_video = str(tmp_path / "extracted.mp4")
    assert extract_motion_video(photo_file, dst_video) is True
    with open(dst_video, "rb") as f:
        assert f.read() == mp4_data


def test_samsung_motion_photo(tmp_path):
    """Test Samsung MotionPhoto_Data marker detection and extraction."""
    mp4_data = create_dummy_mp4()
    marker = b"MotionPhoto_Data"
    jpeg_data = create_dummy_jpeg()
    
    photo_file = str(tmp_path / "samsung.jpg")
    with open(photo_file, "wb") as f:
        f.write(jpeg_data + marker + mp4_data)

    assert is_motion_photo_file(photo_file) is True
    dst_video = str(tmp_path / "extracted.mp4")
    assert extract_motion_video(photo_file, dst_video) is True
    with open(dst_video, "rb") as f:
        assert f.read() == mp4_data


def test_generic_appended_mp4(tmp_path):
    """Test standard JPEG with appended MP4 video."""
    mp4_data = create_dummy_mp4()
    jpeg_data = create_dummy_jpeg()
    
    photo_file = str(tmp_path / "generic.jpg")
    with open(photo_file, "wb") as f:
        f.write(jpeg_data + mp4_data)

    assert is_motion_photo_file(photo_file) is True
    dst_video = str(tmp_path / "extracted.mp4")
    assert extract_motion_video(photo_file, dst_video) is True
    with open(dst_video, "rb") as f:
        assert f.read() == mp4_data


def test_non_motion_photo(tmp_path):
    """Test normal JPEG without motion photo video."""
    jpeg_data = create_dummy_jpeg()
    photo_file = str(tmp_path / "normal.jpg")
    with open(photo_file, "wb") as f:
        f.write(jpeg_data)

    assert is_motion_photo_file(photo_file) is False
    assert get_motion_video_offset(photo_file) is None
    dst_video = str(tmp_path / "extracted.mp4")
    assert extract_motion_video(photo_file, dst_video) is False
    assert not os.path.isfile(dst_video)


def test_paired_motion_video(tmp_path):
    """Test paired external motion video file detection."""
    img_file = str(tmp_path / "IMG_1234.jpg")
    with open(img_file, "wb") as f:
        f.write(create_dummy_jpeg())

    # Initially no paired video
    assert find_paired_motion_video(img_file) is None

    # Create paired MP4
    vid_file = str(tmp_path / "IMG_1234.mp4")
    with open(vid_file, "wb") as f:
        f.write(create_dummy_mp4())

    assert find_paired_motion_video(img_file) == vid_file


def test_image_motion_photo_properties(tmp_path):
    """Test Image class properties for motion photos."""
    mp4_data = create_dummy_mp4()
    jpeg_data = create_dummy_jpeg()
    photo_file = str(tmp_path / "PXL_20230101.jpg")
    with open(photo_file, "wb") as f:
        f.write(jpeg_data + b"MotionPhoto_Data" + mp4_data)

    dest_dir = str(tmp_path / "_build")
    settings = create_settings(source=str(tmp_path), destination=dest_dir)
    img = Image("PXL_20230101.jpg", ".", settings)

    assert img.is_motion_photo is True
    assert img.motion_video_filename == "PXL_20230101.motion.mp4"
    assert img.motion_video_url == "./PXL_20230101.motion.mp4"
    assert img.motion_video_dst_path == os.path.join(dest_dir, ".", "PXL_20230101.motion.mp4")

    # Extract video
    assert img.extract_motion_video() is True
    assert os.path.isfile(img.motion_video_dst_path)
    with open(img.motion_video_dst_path, "rb") as f:
        assert f.read() == mp4_data


def test_motion_photos_setting_disabled(tmp_path):
    """Test disabling motion_photos in settings."""
    mp4_data = create_dummy_mp4()
    jpeg_data = create_dummy_jpeg()
    photo_file = str(tmp_path / "motion.jpg")
    with open(photo_file, "wb") as f:
        f.write(jpeg_data + b"MotionPhoto_Data" + mp4_data)

    settings = create_settings(source=str(tmp_path), destination=str(tmp_path / "dest"), motion_photos=False)
    img = Image("motion.jpg", ".", settings)
    assert img.is_motion_photo is False


def test_gallery_build_with_motion_photo(tmp_path):
    """Test end-to-end gallery build with a motion photo."""
    src_dir = str(tmp_path / "pictures")
    os.makedirs(src_dir, exist_ok=True)
    dst_dir = str(tmp_path / "build")

    # Use Pillow to create a valid JPEG with PIL
    im = PILImage.new("RGB", (300, 200), color="blue")
    photo_path = os.path.join(src_dir, "test_motion.jpg")
    im.save(photo_path, "JPEG")

    # Append dummy MP4 with Samsung marker
    mp4_data = create_dummy_mp4()
    with open(photo_path, "ab") as f:
        f.write(b"MotionPhoto_Data" + mp4_data)

    settings = create_settings(
        source=src_dir,
        destination=dst_dir,
        theme="photobook",
        write_html=True,
    )
    gallery = Gallery(settings)
    gallery.build(force=True)

    # Check that motion video was extracted
    extracted_video = os.path.join(dst_dir, "test_motion.motion.mp4")
    assert os.path.isfile(extracted_video)
    with open(extracted_video, "rb") as f:
        assert f.read() == mp4_data

    # Check HTML contains motion photo attributes and button
    index_html = os.path.join(dst_dir, "index.html")
    assert os.path.isfile(index_html)
    with open(index_html, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'data-is-motion-photo="true"' in html
    assert 'class="motion-photo-btn"' in html
    assert 'test_motion.motion.mp4' in html
    assert 'viewer-motion-btn' in html
    assert 'photobook-motion-video' in html


def test_motion_photo_via_markdown_metadata(tmp_path):
    """Test specifying motion photo via markdown metadata file."""
    src_dir = str(tmp_path / "pictures")
    os.makedirs(src_dir, exist_ok=True)
    dst_dir = str(tmp_path / "build")

    im = PILImage.new("RGB", (300, 200), color="green")
    photo_path = os.path.join(src_dir, "lake.jpg")
    im.save(photo_path, "JPEG")

    # Create motion video file
    video_path = os.path.join(src_dir, "lake_clip.mp4")
    mp4_data = create_dummy_mp4()
    with open(video_path, "wb") as f:
        f.write(mp4_data)

    # Create markdown metadata file specifying motion_video
    md_path = os.path.join(src_dir, "lake.md")
    with open(md_path, "w") as f:
        f.write("Title: Beautiful Lake\nMotion_Video: lake_clip.mp4\n")

    settings = create_settings(source=src_dir, destination=dst_dir, theme="photobook", write_html=True)
    gallery = Gallery(settings)
    gallery.build(force=True)

    extracted_video = os.path.join(dst_dir, "lake.motion.mp4")
    assert os.path.isfile(extracted_video)
    with open(extracted_video, "rb") as f:
        assert f.read() == mp4_data
