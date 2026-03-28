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
     * Fetch image as blob with fallback for file:// protocol
     */
    function fetchImageAsBlob(url) {
        return new Promise(function(resolve, reject) {
            if (!url) {
                reject(new Error('No URL provided'));
                return;
            }

            console.log('Fetching image:', url);

            // Check if this is a file:// URL (local file)
            if (url.startsWith('file://')) {
                console.log('Detected file:// protocol, using XMLHttpRequest');
                loadImageViaXhr(url).then(resolve).catch(function(err) {
                    console.warn('XHR failed, fallback to Image API:', err.message);
                    loadImageViaImage(url).then(resolve).catch(reject);
                });
                return;
            }

            // Try direct fetch for http/https URLs
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
                    convertBlobToJpeg(blob).then(resolve).catch(reject);
                }
            })
            .catch(function(err) {
                console.error('Fetch failed for image:', url, 'error:', err.message);
                reject(err);
            });
        });
    }

    /**
     * Load image via XMLHttpRequest (works for file:// URLs)
     */
    function loadImageViaXhr(url) {
        return new Promise(function(resolve, reject) {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.responseType = 'blob';
            
            xhr.onload = function() {
                if (xhr.status === 200) {
                    const blob = xhr.response;
                    console.log('Loaded via XHR, blob size:', blob.size, 'type:', blob.type);
                    
                    // If it's already a JPEG, use as-is
                    if (blob.type === 'image/jpeg' || url.toLowerCase().endsWith('.jpg')) {
                        const reader = new FileReader();
                        reader.onload = function() {
                            resolve(new Uint8Array(reader.result));
                        };
                        reader.onerror = function() {
                            reject(new Error('Failed to read blob'));
                        };
                        reader.readAsArrayBuffer(blob);
                    } else {
                        // For PNG/WebP, convert to JPEG using canvas
                        convertBlobToJpeg(blob).then(resolve).catch(reject);
                    }
                } else {
                    reject(new Error('XHR failed with status ' + xhr.status));
                }
            };
            
            xhr.onerror = function() {
                reject(new Error('XHR request failed'));
            };
            
            xhr.ontimeout = function() {
                reject(new Error('XHR request timeout'));
            };
            
            xhr.send();
        });
    }

    /**
     * Convert blob to JPEG safely
     */
    function convertBlobToJpeg(blob) {
        return new Promise(function(resolve, reject) {
            // Create an object URL for the blob (safe, no tainting)
            const objectUrl = URL.createObjectURL(blob);
            const img = new Image();
            
            img.onload = function() {
                console.log('Image loaded, size:', img.width, 'x', img.height);
                
                // Create an offscreen canvas
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                
                const ctx = canvas.getContext('2d');
                if (!ctx) {
                    URL.revokeObjectURL(objectUrl);
                    reject(new Error('Failed to get canvas context'));
                    return;
                }
                
                // Draw to canvas
                ctx.drawImage(img, 0, 0);
                
                // Convert to JPEG blob
                canvas.toBlob(function(jpegBlob) {
                    URL.revokeObjectURL(objectUrl);
                    
                    if (!jpegBlob) {
                        reject(new Error('Failed to convert to JPEG'));
                        return;
                    }
                    
                    console.log('Converted to JPEG, size:', jpegBlob.size);
                    const jpegReader = new FileReader();
                    jpegReader.onload = function() {
                        resolve(new Uint8Array(jpegReader.result));
                    };
                    jpegReader.onerror = function() {
                        reject(new Error('Failed to read JPEG'));
                    };
                    jpegReader.readAsArrayBuffer(jpegBlob);
                }, 'image/jpeg', 0.9);
            };
            
            img.onerror = function() {
                URL.revokeObjectURL(objectUrl);
                reject(new Error('Failed to load image for conversion'));
            };
            
            img.src = objectUrl;
        });
    }

    /**
     * Load image via Image API and convert to JPEG (fallback for cross-origin)
     */
    function loadImageViaImage(url) {
        return new Promise(function(resolve, reject) {
            const img = new Image();
            img.crossOrigin = 'Anonymous';
            
            img.onload = function() {
                console.log('Image loaded via Image API, size:', img.width, 'x', img.height);
                
                // Create a canvas with offscreen context
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                
                const ctx = canvas.getContext('2d');
                if (!ctx) {
                    reject(new Error('Failed to get canvas context'));
                    return;
                }
                
                try {
                    ctx.drawImage(img, 0, 0);
                } catch (e) {
                    console.warn('Canvas drawing failed (canvas tainted):', e.message);
                    reject(new Error('Canvas became tainted'));
                    return;
                }
                
                canvas.toBlob(function(jpegBlob) {
                    if (!jpegBlob) {
                        reject(new Error('Failed to convert to JPEG'));
                        return;
                    }
                    
                    console.log('Converted to JPEG, size:', jpegBlob.size);
                    const jpegReader = new FileReader();
                    jpegReader.onload = function() {
                        resolve(new Uint8Array(jpegReader.result));
                    };
                    jpegReader.onerror = function() {
                        reject(new Error('Failed to read JPEG'));
                    };
                    jpegReader.readAsArrayBuffer(jpegBlob);
                }, 'image/jpeg', 0.9);
            };
            
            img.onerror = function() {
                reject(new Error('Failed to load image'));
            };
            
            img.src = url;
        });
    }

    /**
     * Create EPUB 3.0 package.opf metadata file
     */
    function createPackageOpf(title, uuid, mediaList) {
        let manifestItems = '';
        let spineItems = '';

        // Add nav.xhtml to manifest
        manifestItems += '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n';

        mediaList.forEach(function(media, idx) {
            if (media.isImage) {
                const imgId = 'img_' + idx;
                manifestItems += '    <item id="' + imgId + '" href="images/image_' + idx + '.jpg" media-type="image/jpeg"/>\n';
            }
            const pageId = 'page_' + idx;
            manifestItems += '    <item id="' + pageId + '" href="xhtml/page_' + idx + '.xhtml" media-type="application/xhtml+xml"/>\n';
            spineItems += '    <itemref idref="' + pageId + '"/>\n';
        });

        manifestItems += '    <item id="style" href="style/style.css" media-type="text/css"/>\n';

        const nowDate = new Date().toISOString();

        return `<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uuid" xml:lang="en">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>${escapeXml(title)}</dc:title>
    <dc:creator>Sigal Photo Gallery</dc:creator>
    <dc:language>en</dc:language>
    <dc:issued>${nowDate}</dc:issued>
    <dc:identifier id="uuid">${uuid}</dc:identifier>
  </metadata>
  <manifest>
${manifestItems}  </manifest>
  <spine>
${spineItems}  </spine>
</package>`;
    }

    /**
     * Create EPUB 3.0 navigation document (nav.xhtml)
     */
    function createNavXhtml(title, mediaList) {
        let navItems = '';

        mediaList.forEach(function(media, idx) {
            const pageNum = idx + 1;
            navItems += `    <li><a href="xhtml/page_${idx}.xhtml">${escapeXml(media.title)}</a></li>\n`;
        });

        return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
  <head>
    <title>${escapeXml(title)}</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" type="text/css" href="style/style.css"/>
  </head>
  <body>
    <nav epub:type="toc" id="toc">
      <h1>Table of Contents</h1>
      <ol>
${navItems}      </ol>
    </nav>
  </body>
</html>`;
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
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
  <head>
    <title>${escapeXml(media.title)}</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" type="text/css" href="../style/style.css"/>
  </head>
  <body>
    <div class="page" epub:type="bodymatter chapter">
      <div class="page-content">
${mediaHtml}
        <div class="page-caption">
          <h1 class="page-title">${escapeXml(media.title)}</h1>
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
  <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
</container>`);

            // Create OEBPS directory structure
            const oebps = zip.folder('OEBPS');
            oebps.file('package.opf', createPackageOpf(title, uuid, mediaList));
            oebps.file('nav.xhtml', createNavXhtml(title, mediaList));

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
                console.log('EPUB 3.0 will contain:');
                console.log('  - Metadata files: mimetype=' + structure.mimetype + ', container=' + structure.container + ', opf=' + structure.opf);
                console.log('  - Navigation: nav=' + structure.nav + ', css=' + structure.css);
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
            nav: false,
            css: false,
            images: 0,
            xhtml: 0
        };

        zip.forEach(function(relativePath, file) {
            console.log('ZIP contains:', relativePath, '(' + file.dir + ')');
            
            if (relativePath === 'mimetype') structure.mimetype = true;
            if (relativePath === 'META-INF/container.xml') structure.container = true;
            if (relativePath === 'OEBPS/package.opf') structure.opf = true;
            if (relativePath === 'OEBPS/nav.xhtml') structure.nav = true;
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
