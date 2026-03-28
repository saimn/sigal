/**
 * Photobook Theme EPUB Export
 * Generates and exports the photo book as an EPUB file
 */

(function() {
    'use strict';

    // Check if JSZip is available (will be loaded via CDN)
    const checkJsZip = function() {
        return typeof JSZip !== 'undefined';
    };

    /**
     * Generate a UUID-like identifier for EPUB
     */
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0,
                v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Get the album title from the page
     */
    function getAlbumTitle() {
        const heading = document.querySelector('.photobook-header h1 a') || document.querySelector('h1');
        if (heading) {
            return heading.textContent.trim();
        }
        return 'Photo Book';
    }

    /**
     * Get media data from the continuous book container
     */
    function collectMediaData() {
        const mediaList = [];
        const mediaElements = document.querySelectorAll('.book-entry');

        mediaElements.forEach(function(entry, index) {
            const mediaDiv = entry.querySelector('.book-media');
            const captionDiv = entry.querySelector('.book-caption');

            if (mediaDiv) {
                const img = mediaDiv.querySelector('.book-image');
                const video = mediaDiv.querySelector('.book-video');
                const mediaUrl = img ? img.src : (video ? video.querySelector('source')?.src : null);

                const title = captionDiv ? captionDiv.querySelector('h2')?.textContent.trim() : 'Photo ' + (index + 1);
                const description = captionDiv ? captionDiv.querySelector('.book-description')?.innerHTML : '';
                const filename = captionDiv ? captionDiv.querySelector('.book-filename')?.textContent : '';
                const exifHtml = captionDiv ? captionDiv.querySelector('.book-exif')?.innerHTML : '';

                mediaList.push({
                    index: index,
                    url: mediaUrl,
                    title: title,
                    description: description,
                    filename: filename,
                    exif: exifHtml,
                    isImage: !!img,
                    isVideo: !!video
                });
            }
        });

        return mediaList;
    }

    /**
     * Convert image URL to base64 (for local images)
     */
    function imageToBase64(url) {
        return new Promise(function(resolve, reject) {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();

            img.crossOrigin = 'Anonymous';
            img.onload = function() {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
                const base64 = dataUrl.split(',')[1];
                resolve(base64);
            };

            img.onerror = function() {
                reject(new Error('Failed to load image: ' + url));
            };

            img.src = url;
        });
    }

    /**
     * Create EPUB package.opf metadata file
     */
    function createPackageOpf(title, uuid, mediaList) {
        let manifestItems = '';
        let spineItems = '';

        mediaList.forEach(function(media, idx) {
            if (media.isImage) {
                const imgId = 'img_' + idx;
                manifestItems += '    <item id="' + imgId + '" href="images/image_' + idx + '.jpg" media-type="image/jpeg"/>\n';
            }
            const pageId = 'page_' + idx;
            manifestItems += '    <item id="' + pageId + '" href="xhtml/page_' + idx + '.xhtml" media-type="application/xhtml+xml"/>\n';
            spineItems += '    <itemref idref="' + pageId + '"/>\n';
        });

        manifestItems += '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbook+xml"/>\n';
        manifestItems += '    <item id="style" href="style/style.css" media-type="text/css"/>\n';

        const nowDate = new Date().toISOString();

        return `<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="uuid" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>${escapeXml(title)}</dc:title>
    <dc:creator>Sigal Photo Gallery</dc:creator>
    <dc:language>en</dc:language>
    <dc:date>${nowDate}</dc:date>
    <dc:identifier id="uuid">${uuid}</dc:identifier>
  </metadata>
  <manifest>
${manifestItems}  </manifest>
  <spine toc="ncx">
${spineItems}  </spine>
</package>`;
    }

    /**
     * Create EPUB table of contents (toc.ncx)
     */
    function createTocNcx(title, mediaList) {
        let navPoints = '';

        mediaList.forEach(function(media, idx) {
            const pageNum = idx + 1;
            navPoints += `    <navPoint id="navpoint_${idx}" playOrder="${pageNum}">
      <navLabel>
        <text>${escapeXml(media.title)}</text>
      </navLabel>
      <content src="xhtml/page_${idx}.xhtml"/>
    </navPoint>\n`;
        });

        return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
  <head>
    <meta name="dtb:uid" content="${generateUUID()}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>${escapeXml(title)}</text>
  </docTitle>
  <navMap>
${navPoints}  </navMap>
</ncx>`;
    }

    /**
     * Create CSS for EPUB pages
     */
    function createCss() {
        return `/* Photobook EPUB Styles */
* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    background-color: #ffffff;
    color: #333333;
    line-height: 1.6;
}

body {
    font-size: 14px;
}

.page {
    page-break-after: always;
    break-after: page;
    padding: 20px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.page-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.page-media {
    display: flex;
    justify-content: center;
    align-items: center;
    max-height: 60vh;
}

.page-media img {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
}

.page-caption {
    flex: 1;
}

.page-title {
    font-size: 20px;
    font-weight: 700;
    margin: 10px 0 15px 0;
    color: #222222;
}

.page-description {
    margin: 10px 0;
    font-size: 14px;
    line-height: 1.6;
    color: #444444;
    background-color: #f9f9f9;
    padding: 10px;
    border-left: 3px solid #cccccc;
}

.page-filename {
    margin: 10px 0;
    padding: 8px;
    background-color: #f5f5f5;
    border-radius: 3px;
    font-size: 12px;
    border-left: 2px solid #cccccc;
    word-break: break-all;
}

.page-exif {
    margin: 10px 0;
    font-size: 13px;
}

.exif-item {
    margin: 5px 0;
    padding: 5px;
    background-color: #f5f5f5;
    border-radius: 2px;
    border-left: 2px solid #cccccc;
}

.exif-label {
    font-weight: 500;
    color: #333333;
}

.exif-value {
    color: #666666;
}`;
    }

    /**
     * Create an XHTML page for each media
     */
    function createXhtmlPage(media, idx) {
        const pageNum = idx + 1;
        let mediaHtml = '';

        if (media.isImage) {
            mediaHtml = `    <div class="page-media">
      <img src="../images/image_${idx}.jpg" alt="${escapeXml(media.title)}"/>
    </div>`;
        }

        let descriptionHtml = '';
        if (media.description) {
            descriptionHtml = `    <div class="page-description">${media.description}</div>`;
        }

        let filenameHtml = '';
        if (media.filename && media.filename.trim()) {
            filenameHtml = `    <div class="page-filename">${escapeXml(media.filename)}</div>`;
        }

        let exifHtml = '';
        if (media.exif && media.exif.trim()) {
            exifHtml = `    <div class="page-exif">${media.exif}</div>`;
        }

        return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>${escapeXml(media.title)}</title>
    <link rel="stylesheet" type="text/css" href="../style/style.css"/>
  </head>
  <body>
    <div class="page" epub:type="bodymatter chapter">
      <div class="page-content">
${mediaHtml}
        <div class="page-caption">
          <div class="page-title">${escapeXml(media.title)}</div>
${descriptionHtml}
${filenameHtml}
${exifHtml}
        </div>
      </div>
    </div>
  </body>
</html>`;
    }

    /**
     * Escape XML special characters
     */
    function escapeXml(str) {
        if (!str) return '';
        return str.replace(/[<>&'"]/g, function(c) {
            switch (c) {
                case '<': return '&lt;';
                case '>': return '&gt;';
                case '&': return '&amp;';
                case "'": return '&apos;';
                case '"': return '&quot;';
            }
        });
    }

    /**
     * Load JSZip library dynamically if not present
     */
    function loadJsZip() {
        return new Promise(function(resolve, reject) {
            if (checkJsZip()) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
            script.onload = function() {
                if (checkJsZip()) {
                    resolve();
                } else {
                    reject(new Error('JSZip failed to load'));
                }
            };
            script.onerror = function() {
                reject(new Error('Failed to load JSZip library'));
            };
            document.head.appendChild(script);
        });
    }

    /**
     * Main export function
     */
    function exportToEpub() {
        const exportBtn = document.getElementById('epub-export-btn');
        if (!exportBtn) return;

        // Disable button during export
        exportBtn.disabled = true;
        exportBtn.textContent = '⏳ Generating EPUB...';

        loadJsZip().then(function() {
            const title = getAlbumTitle();
            const uuid = generateUUID();
            const mediaList = collectMediaData();

            if (mediaList.length === 0) {
                alert('No media found to export');
                exportBtn.disabled = false;
                exportBtn.textContent = '📕 Export EPUB';
                return;
            }

            const zip = new JSZip();

            // Add mimetype (must be first and uncompressed)
            zip.file('mimetype', 'application/epub+zip', { compression: 'STORE' });

            // Create META-INF directory and container.xml
            zip.folder('META-INF').file('container.xml', `<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
</container>`);

            // Create OEBPS directory structure
            const oebps = zip.folder('OEBPS');
            oebps.file('content.opf', createPackageOpf(title, uuid, mediaList));
            oebps.file('toc.ncx', createTocNcx(title, mediaList));

            // Create style directory
            oebps.folder('style').file('style.css', createCss());

            // Create images directory and xhtml directory
            const imagesFolder = oebps.folder('images');
            const xhtmlFolder = oebps.folder('xhtml');

            // Process media and create XHTML pages
            const imagePromises = mediaList.map(function(media, idx) {
                // Create XHTML page
                xhtmlFolder.file('page_' + idx + '.xhtml', createXhtmlPage(media, idx));

                // Process image if available
                if (media.isImage && media.url) {
                    return imageToBase64(media.url).then(function(base64Data) {
                        const binaryString = atob(base64Data);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {
                            bytes[i] = binaryString.charCodeAt(i);
                        }
                        imagesFolder.file('image_' + idx + '.jpg', bytes);
                    }).catch(function(err) {
                        console.warn('Failed to load image ' + idx + ':', err);
                    });
                }
                return Promise.resolve();
            });

            Promise.all(imagePromises).then(function() {
                // Generate EPUB file
                zip.generateAsync({ type: 'blob', streamFiles: true }).then(function(blob) {
                    // Create download link
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = title.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '') + '.epub';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);

                    // Re-enable button
                    exportBtn.disabled = false;
                    exportBtn.textContent = '📕 Export EPUB';
                    alert('EPUB exported successfully!');
                }).catch(function(err) {
                    console.error('Error generating EPUB:', err);
                    alert('Error generating EPUB: ' + err.message);
                    exportBtn.disabled = false;
                    exportBtn.textContent = '📕 Export EPUB';
                });
            }).catch(function(err) {
                console.error('Error processing images:', err);
                alert('Error processing images: ' + err.message);
                exportBtn.disabled = false;
                exportBtn.textContent = '📕 Export EPUB';
            });
        }).catch(function(err) {
            console.error('Error loading JSZip:', err);
            alert('Error: Could not load required library. Please check your internet connection.\n' + err.message);
            exportBtn.disabled = false;
            exportBtn.textContent = '📕 Export EPUB';
        });
    }

    /**
     * Initialize EPUB export on page load
     */
    function init() {
        const exportBtn = document.getElementById('epub-export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportToEpub);
            exportBtn.addEventListener('touchend', function(e) {
                e.preventDefault();
                exportToEpub();
            });
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export public API
    window.PhotobookEpub = {
        exportToEpub: exportToEpub
    };

})();
