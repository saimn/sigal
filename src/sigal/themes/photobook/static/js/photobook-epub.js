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
     * Convert relative URL to absolute URL
     */
    function getAbsoluteUrl(url) {
        if (!url) return null;
        if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
            return url;
        }
        // Create absolute URL from relative path
        try {
            const baseUrl = new URL('.', window.location.href).href;
            const absoluteUrl = new URL(url, baseUrl).href;
            console.log('Converted URL:', url, '→', absoluteUrl);
            return absoluteUrl;
        } catch (e) {
            console.warn('Failed to parse URL:', url, e.message);
            // Fallback: try simple concatenation
            const baseUrl = window.location.protocol + '//' + window.location.host;
            const basePath = window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/'));
            return baseUrl + basePath + (url.startsWith('/') ? url : '/' + url);
        }
    }

    /**
     * Get media data from the continuous book container
     */
    function collectMediaData() {
        const mediaList = [];
        const mediaElements = document.querySelectorAll('.book-entry');

        console.log('Found', mediaElements.length, 'book entries');

        mediaElements.forEach(function(entry, index) {
            const mediaDiv = entry.querySelector('.book-media');
            const captionDiv = entry.querySelector('.book-caption');

            if (mediaDiv) {
                const img = mediaDiv.querySelector('.book-image');
                const video = mediaDiv.querySelector('.book-video');
                let mediaUrl = null;
                
                if (img) {
                    mediaUrl = img.src;
                    console.log('Entry', index, ': Found image:', mediaUrl);
                } else if (video) {
                    const source = video.querySelector('source');
                    if (source) {
                        mediaUrl = source.src;
                        console.log('Entry', index, ': Found video:', mediaUrl);
                    }
                }

                // Convert to absolute URL
                mediaUrl = getAbsoluteUrl(mediaUrl);

                const title = captionDiv ? (captionDiv.querySelector('h2')?.textContent.trim() || 'Photo ' + (index + 1)) : 'Photo ' + (index + 1);
                const description = captionDiv ? (captionDiv.querySelector('.book-description')?.innerHTML || '') : '';
                const filename = captionDiv ? (captionDiv.querySelector('.book-filename')?.textContent || '') : '';
                const exifHtml = captionDiv ? (captionDiv.querySelector('.book-exif')?.innerHTML || '') : '';

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

        console.log('Collected media:', mediaList.length, 'items');
        console.log('  Images:', mediaList.filter(m => m.isImage).length);
        console.log('  Videos:', mediaList.filter(m => m.isVideo).length);
        mediaList.forEach(function(m, idx) {
            console.log('  [' + idx + ']', 'Type: ' + (m.isImage ? 'IMAGE' : 'VIDEO'), 'URL:', m.url);
        });
        
        return mediaList;
    }

    /**
     * Fetch image as blob with fallback
     */
    function fetchImageAsBlob(url) {
        return new Promise(function(resolve, reject) {
            if (!url) {
                reject(new Error('No URL provided'));
                return;
            }

            console.log('Fetching image:', url);

            // Try direct fetch first
            fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'image/*'
                },
                mode: 'cors',
                credentials: 'same-origin'
            })
            .then(function(response) {
                if (!response.ok) {
                    console.warn('HTTP ' + response.status + ' for image:', url);
                    throw new Error('HTTP ' + response.status);
                }
                console.log('Response headers:', response.headers.get('content-type'), 'size:', response.headers.get('content-length'));
                return response.blob();
            })
            .then(function(blob) {
                console.log('Got blob, size:', blob.size, 'type:', blob.type);
                
                if (blob.size === 0) {
                    throw new Error('Empty blob received');
                }

                // If it's a JPEG, use as-is
                if (blob.type === 'image/jpeg' || url.toLowerCase().endsWith('.jpg')) {
                    const reader = new FileReader();
                    reader.onload = function() {
                        resolve(new Uint8Array(reader.result));
                    };
                    reader.onerror = function() {
                        reject(new Error('Failed to read JPEG blob'));
                    };
                    reader.readAsArrayBuffer(blob);
                } else {
                    // For other formats (PNG, WebP, etc.), convert to JPEG
                    convertImageToJpeg(blob).then(resolve).catch(reject);
                }
            })
            .catch(function(err) {
                console.error('Fetch failed for image:', url, 'error:', err.message);
                reject(err);
            });
        });
    }

    /**
     * Convert image blob to JPEG using canvas
     */
    function convertImageToJpeg(blob) {
        return new Promise(function(resolve, reject) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    
                    canvas.toBlob(function(jpegBlob) {
                        if (!jpegBlob) {
                            reject(new Error('Failed to convert to JPEG'));
                            return;
                        }
                        
                        const jpegReader = new FileReader();
                        jpegReader.onload = function() {
                            resolve(new Uint8Array(jpegReader.result));
                        };
                        jpegReader.onerror = function() {
                            reject(new Error('Failed to read JPEG data'));
                        };
                        jpegReader.readAsArrayBuffer(jpegBlob);
                    }, 'image/jpeg', 0.9);
                };
                
                img.onerror = function() {
                    reject(new Error('Failed to load image for conversion'));
                };
                
                img.src = e.target.result;
            };
            
            reader.onerror = function() {
                reject(new Error('Failed to read image blob'));
            };
            
            reader.readAsDataURL(blob);
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

        console.log('Starting EPUB export...');

        // Disable button during export
        exportBtn.disabled = true;
        exportBtn.textContent = '⏳ Generating EPUB...';

        loadJsZip().then(function() {
            console.log('JSZip loaded successfully');
            const title = getAlbumTitle();
            const uuid = generateUUID();
            console.log('Album title:', title);
            
            const mediaList = collectMediaData();

            if (mediaList.length === 0) {
                alert('No media found to export');
                exportBtn.disabled = false;
                exportBtn.textContent = '📕 Export EPUB';
                return;
            }

            console.log('Total media items:', mediaList.length);
            console.log('Images:', mediaList.filter(m => m.isImage).length);
            console.log('Videos:', mediaList.filter(m => m.isVideo).length);

            const zip = new JSZip();

            // Add mimetype (must be first and uncompressed)
            zip.file('mimetype', 'application/epub+zip', { compression: 'STORE' });

            // Create META-INF directory and container.xml
            zip.folder('META-INF').file('container.xml', `<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
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
                    return fetchImageAsBlob(media.url).then(function(imageBytes) {
                        console.log('Successfully loaded image', idx, 'size:', imageBytes.length);
                        imagesFolder.file('image_' + idx + '.jpg', imageBytes);
                    }).catch(function(err) {
                        console.warn('Failed to load image ' + idx + ':', err.message);
                        // Continue without this image
                    });
                }
                return Promise.resolve();
            });

            console.log('Starting image download, total images:', mediaList.filter(m => m.isImage).length);

            Promise.all(imagePromises).then(function() {
                console.log('All images processed, generating EPUB...');
                
                // Validate structure
                const structure = validateZipStructure(zip);
                console.log('EPUB will contain:');
                console.log('  - Metadata files: mimetype=' + structure.mimetype + ', container=' + structure.container + ', opf=' + structure.opf);
                console.log('  - Navigation: ncx=' + structure.ncx + ', css=' + structure.css);
                console.log('  - Content: images=' + structure.images + ', xhtml pages=' + structure.xhtml);

                // Generate EPUB file
                zip.generateAsync({ type: 'blob', streamFiles: true }).then(function(blob) {
                    console.log('EPUB generated successfully');
                    console.log('  File size:', blob.size, 'bytes', '(' + Math.round(blob.size / 1024) + ' KB)');
                    console.log('  MIME type:', blob.type);
                    
                    if (blob.size < 1000) {
                        console.warn('WARNING: Generated file is very small. This might indicate a problem with image inclusion.');
                    }
                    
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
                    
                    const msg = 'EPUB exported successfully!\n' +
                                'Size: ' + Math.round(blob.size / 1024) + ' KB\n' +
                                'Images included: ' + structure.images + '\n' +
                                'Pages: ' + structure.xhtml;
                    alert(msg);
                    console.log(msg.replace(/\n/g, ' | '));
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

    /**
     * Validate and log ZIP content structure
     */
    function validateZipStructure(zip) {
        const structure = {
            mimetype: false,
            container: false,
            opf: false,
            ncx: false,
            css: false,
            images: 0,
            xhtml: 0
        };

        zip.forEach(function(relativePath, file) {
            console.log('ZIP contains:', relativePath, '(' + file.dir + ')');
            
            if (relativePath === 'mimetype') structure.mimetype = true;
            if (relativePath === 'META-INF/container.xml') structure.container = true;
            if (relativePath === 'OEBPS/content.opf') structure.opf = true;
            if (relativePath === 'OEBPS/toc.ncx') structure.ncx = true;
            if (relativePath === 'OEBPS/style/style.css') structure.css = true;
            if (relativePath.startsWith('OEBPS/images/')) structure.images++;
            if (relativePath.startsWith('OEBPS/xhtml/')) structure.xhtml++;
        });

        console.log('ZIP Structure validation:', structure);
        return structure;
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
