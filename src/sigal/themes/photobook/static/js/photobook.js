/**
 * Photobook Theme JavaScript
 * Handles photo book paging, view switching, and navigation
 */

(function() {
    'use strict';

    // Configuration - can be customized via settings
    const config = {
        photosPerPage: 1,  // Default photos per page (can be set in sigal config)
        enableKeyboard: true,
        enableOutlineClickNavigation: true,
        mapProvider: 'openstreetmap'  // 'openstreetmap' or 'googlemaps'
    };

    let currentPage = 0;
    let totalPages = 0;
    let pages = [];
    let currentView = 'outline'; // 'outline', 'slides', or 'book'
    let viewerOpen = false;
    let viewerCurrentIndex = 0;
    let viewerMediaData = [];

    /**
     * Add both click and touch handlers to ensure mobile compatibility
     */
    function addClickHandler(element, callback) {
        if (!element) return;
        element.addEventListener('click', callback);
        // Also handle touch events for better Android Chrome compatibility
        element.addEventListener('touchend', function(e) {
            e.preventDefault();
            callback.call(this);
        });
    }

    /**
     * Initialize the photobook on page load
     */
    function init() {
        // Get elements
        const outlineBtn = document.getElementById('outline-btn');
        const slidesBtn = document.getElementById('slides-btn');
        const bookBtn = document.getElementById('book-btn');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const outlineView = document.getElementById('outline-view');
        const slidesView = document.getElementById('slides-view');
        const bookView = document.getElementById('book-view');
        const photoContainer = document.getElementById('photobook-container');

        // Initialize pages array for slides view
        if (photoContainer) {
            pages = Array.from(photoContainer.querySelectorAll('.photobook-page'));
            totalPages = pages.length;
            updatePageCounter();

            // Show first page by default
            if (pages.length > 0) {
                showPage(0);
            }
        }

        // Event listeners for view switching - using separate if blocks for robustness
        if (outlineBtn) {
            addClickHandler(outlineBtn, function() {
                switchView('outline', outlineBtn, slidesBtn, bookBtn, outlineView, slidesView, bookView);
            });
        }

        if (slidesBtn) {
            addClickHandler(slidesBtn, function() {
                switchView('slides', outlineBtn, slidesBtn, bookBtn, outlineView, slidesView, bookView);
            });
        }

        if (bookBtn) {
            addClickHandler(bookBtn, function() {
                switchView('book', outlineBtn, slidesBtn, bookBtn, outlineView, slidesView, bookView);
            });
        }

        // Event listeners for navigation (slides view only)
        if (prevBtn) {
            addClickHandler(prevBtn, previousPage);
        }
        if (nextBtn) {
            addClickHandler(nextBtn, nextPage);
        }

        // Keyboard navigation
        if (config.enableKeyboard) {
            document.addEventListener('keydown', handleKeyboard);
        }

        // Outline click navigation
        if (config.enableOutlineClickNavigation) {
            setupOutlineNavigation();
        }

        // Setup media viewer
        setupMediaViewer();

        // Setup GPS link handlers
        setupGpsLinks();
    }

    /**
     * Switch between outline, slides and book views
     */
    function switchView(view, outlineBtn, slidesBtn, bookBtn, outlineView, slidesView, bookView) {
        currentView = view;

        // Hide all views
        outlineView.classList.remove('active');
        slidesView.classList.remove('active');
        bookView.classList.remove('active');
        
        // Remove active state from buttons
        outlineBtn.classList.remove('active');
        slidesBtn.classList.remove('active');
        bookBtn.classList.remove('active');

        // Show selected view
        if (view === 'outline') {
            outlineView.classList.add('active');
            outlineBtn.classList.add('active');
        } else if (view === 'slides') {
            slidesView.classList.add('active');
            slidesBtn.classList.add('active');
            // Reset to first slide when switching to slides view
            showPage(0);
        } else if (view === 'book') {
            bookView.classList.add('active');
            bookBtn.classList.add('active');
        }
    }

    /**
     * Show a specific page
     */
    function showPage(pageIndex) {
        // Validate page index
        if (pageIndex < 0 || pageIndex >= pages.length) {
            return;
        }

        // Hide all pages
        pages.forEach(function(page) {
            page.classList.remove('active');
        });

        // Show current page
        if (pages[pageIndex]) {
            pages[pageIndex].classList.add('active');
            currentPage = pageIndex;
            updatePageCounter();

            // Scroll to page
            pages[pageIndex].scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /**
     * Navigate to next page
     */
    function nextPage() {
        if (currentPage < pages.length - 1) {
            showPage(currentPage + 1);
        }
    }

    /**
     * Navigate to previous page
     */
    function previousPage() {
        if (currentPage > 0) {
            showPage(currentPage - 1);
        }
    }

    /**
     * Update page counter display
     */
    function updatePageCounter() {
        const currentPageSpan = document.getElementById('current-page');
        if (currentPageSpan) {
            currentPageSpan.textContent = currentPage + 1;
        }
    }

    /**
     * Handle keyboard navigation
     */
    function handleKeyboard(event) {
        // Handle Escape for closing viewer
        if (event.key === 'Escape' && viewerOpen) {
            closeMediaViewer();
            event.preventDefault();
            return;
        }

        // If viewer is open, handle viewer navigation only
        if (viewerOpen) {
            switch(event.key) {
                case 'ArrowRight':
                case ' ':
                    viewerNext();
                    event.preventDefault();
                    break;
                case 'ArrowLeft':
                    viewerPrevious();
                    event.preventDefault();
                    break;
                case 'Home':
                    openMediaViewerAtIndex(0);
                    event.preventDefault();
                    break;
                case 'End':
                    openMediaViewerAtIndex(viewerMediaData.length - 1);
                    event.preventDefault();
                    break;
            }
            return;
        }

        // Handle slides view navigation
        if (currentView !== 'slides') {
            return;
        }

        switch(event.key) {
            case 'ArrowRight':
            case ' ':
                nextPage();
                event.preventDefault();
                break;
            case 'ArrowLeft':
                previousPage();
                event.preventDefault();
                break;
            case 'Home':
                showPage(0);
                event.preventDefault();
                break;
            case 'End':
                showPage(pages.length - 1);
                event.preventDefault();
                break;
        }
    }

    /**
     * Setup outline item click navigation
     */
    function setupOutlineNavigation() {
        const outlineItems = document.querySelectorAll('.outline-item');
        const slidesBtn = document.getElementById('slides-btn');

        outlineItems.forEach(function(item, index) {
            addClickHandler(item, function() {
                // Switch to slides view
                if (slidesBtn) {
                    slidesBtn.click();
                }
                // Show corresponding page
                setTimeout(function() {
                    showPage(index);
                }, 100);
            });
        });
    }

    /**
     * Setup GPS link handlers
     */
    function setupGpsLinks() {
        // Handle GPS links in page captions
        const gpsLinks = document.querySelectorAll('.gps-link');
        gpsLinks.forEach(function(link) {
            addClickHandler(link, function(e) {
                if (e) {
                    e.preventDefault();
                }
                const lat = parseFloat(this.getAttribute('data-gps-lat'));
                const lon = parseFloat(this.getAttribute('data-gps-lon'));
                
                if (!isNaN(lat) && !isNaN(lon)) {
                    const url = getGpsUrl(lat, lon);
                    window.open(url, '_blank');
                }
            });
        });
    }

    /**
     * Setup media viewer
     */
    function setupMediaViewer() {
        // Collect media data from pages
        viewerMediaData = Array.from(document.querySelectorAll('.photobook-page')).map(function(page) {
            const metadata = page.querySelector('.media-metadata');
            
            // Extract description
            let description = '';
            if (metadata) {
                const descElem = metadata.querySelector('.media-description-data');
                if (descElem) {
                    description = descElem.innerHTML;
                }
            }
            
            // Extract EXIF data
            let exifData = {
                datetime: '',
                camera: '',
                iso: '',
                exposure: '',
                fstop: '',
                focal: '',
                gps: null
            };
            
            if (metadata) {
                const exifElem = metadata.querySelector('.media-exif-data');
                if (exifElem) {
                    const datetimeElem = exifElem.querySelector('.exif-datetime');
                    if (datetimeElem) exifData.datetime = datetimeElem.textContent.trim();
                    
                    const cameraElem = exifElem.querySelector('.exif-camera');
                    if (cameraElem) exifData.camera = cameraElem.textContent.trim();
                    
                    const settingsElem = exifElem.querySelector('.exif-settings');
                    if (settingsElem) {
                        const isoElem = settingsElem.querySelector('.exif-iso');
                        if (isoElem) exifData.iso = isoElem.textContent.trim();
                        
                        const exposureElem = settingsElem.querySelector('.exif-exposure');
                        if (exposureElem) exifData.exposure = exposureElem.textContent.trim();
                        
                        const fstopElem = settingsElem.querySelector('.exif-fstop');
                        if (fstopElem) exifData.fstop = fstopElem.textContent.trim();
                        
                        const focalElem = settingsElem.querySelector('.exif-focal');
                        if (focalElem) exifData.focal = focalElem.textContent.trim();
                    }
                    
                    const gpsElem = exifElem.querySelector('.exif-gps');
                    if (gpsElem) {
                        exifData.gps = {
                            lat: parseFloat(gpsElem.getAttribute('data-lat')),
                            lon: parseFloat(gpsElem.getAttribute('data-lon')),
                            coords: gpsElem.textContent.trim()
                        };
                    }
                }
            }
            
            return {
                url: page.getAttribute('data-media-url'),
                type: page.getAttribute('data-media-type'),
                mime: page.getAttribute('data-media-mime'),
                title: page.getAttribute('data-media-title') || 'Unknown',
                filename: page.getAttribute('data-media-filename') || '',
                description: description,
                exif: exifData
            };
        });

        // Setup click handlers for clickable media
        const clickableMedia = document.querySelectorAll('.clickable-media');
        clickableMedia.forEach(function(media, index) {
            addClickHandler(media, function() {
                openMediaViewerAtIndex(index);
            });

            // Keyboard support for clickable media
            media.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    openMediaViewerAtIndex(index);
                    e.preventDefault();
                }
            });
        });

        // Setup viewer controls
        const viewerClose = document.getElementById('viewer-close');
        const viewerPrevBtn = document.getElementById('viewer-prev');
        const viewerNextBtn = document.getElementById('viewer-next');
        const mediaViewer = document.getElementById('media-viewer');

        if (viewerClose) {
            addClickHandler(viewerClose, closeMediaViewer);
        }

        if (viewerPrevBtn) {
            addClickHandler(viewerPrevBtn, viewerPrevious);
        }

        if (viewerNextBtn) {
            addClickHandler(viewerNextBtn, viewerNext);
        }

        // Close viewer when clicking on overlay
        if (mediaViewer) {
            mediaViewer.addEventListener('click', function(e) {
                if (e.target === mediaViewer) {
                    closeMediaViewer();
                }
            });
            // Also handle touch on overlay
            mediaViewer.addEventListener('touchend', function(e) {
                if (e.target === mediaViewer) {
                    e.preventDefault();
                    closeMediaViewer();
                }
            });
        }
    }

    /**
     * Open media viewer at specific index
     */
    function openMediaViewerAtIndex(index) {
        if (index < 0 || index >= viewerMediaData.length) {
            return;
        }

        viewerCurrentIndex = index;
        const media = viewerMediaData[index];

        // Get viewer elements
        const mediaViewer = document.getElementById('media-viewer');
        const viewerImage = document.getElementById('viewer-image');
        const viewerVideo = document.getElementById('viewer-video');
        const viewerVideoSource = document.getElementById('viewer-video-source');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerCounter = document.getElementById('viewer-counter');

        if (!mediaViewer || !viewerImage || !viewerVideo) {
            return;
        }

        // Hide both and show appropriate one
        viewerImage.style.display = 'none';
        viewerVideo.style.display = 'none';

        // Update media display and viewer links
        const viewerImageLink = document.getElementById('viewer-image-link');
        if (media.type === 'image') {
            viewerImage.src = media.url;
            viewerImage.style.display = 'block';
            if (viewerImageLink) {
                viewerImageLink.href = media.url;
            }
        } else if (media.type === 'video') {
            viewerVideoSource.src = media.url;
            viewerVideoSource.type = media.mime;
            viewerVideo.load();
            viewerVideo.style.display = 'block';
            if (viewerImageLink) {
                // disable image link for videos
                viewerImageLink.href = '#';
            }
        }

        // Update info
        if (viewerTitle) {
            viewerTitle.textContent = media.title;
        }

        if (viewerCounter) {
            viewerCounter.textContent = (index + 1) + ' / ' + viewerMediaData.length;
        }

        // Update description section
        const descriptionSection = document.getElementById('viewer-description-section');
        const descriptionContent = document.getElementById('viewer-description');
        if (descriptionSection && descriptionContent) {
            if (media.description && media.description.trim()) {
                descriptionContent.innerHTML = media.description;
                descriptionSection.style.display = 'block';
            } else {
                descriptionSection.style.display = 'none';
            }
        }

        // Update filename section and make it a link to the full-size file
        const filenameSection = document.getElementById('viewer-filename-section');
        const filenameContent = document.getElementById('viewer-filename');
        const filenameLink = document.getElementById('viewer-filename-link');
        if (filenameSection && filenameContent && filenameLink) {
            if (media.filename) {
                filenameContent.textContent = media.filename;
                filenameLink.href = media.url || '#';
                filenameSection.style.display = 'block';
            } else {
                filenameSection.style.display = 'none';
            }
        }

        // Update EXIF section
        const exifSection = document.getElementById('viewer-exif-section');
        const exifItems = document.getElementById('viewer-exif-items');
        if (exifSection && exifItems) {
            exifItems.innerHTML = '';
            const exif = media.exif;
            let hasExif = false;

            // Add datetime
            if (exif.datetime) {
                exifItems.innerHTML += '<div class="viewer-exif-item"><span class="viewer-exif-label">Date:</span> <span class="viewer-exif-value">' + escapeHtml(exif.datetime) + '</span></div>';
                hasExif = true;
            }

            // Add camera
            if (exif.camera) {
                exifItems.innerHTML += '<div class="viewer-exif-item"><span class="viewer-exif-label">Camera:</span> <span class="viewer-exif-value">' + escapeHtml(exif.camera) + '</span></div>';
                hasExif = true;
            }

            // Add settings
            const settings = [];
            if (exif.iso) settings.push('ISO ' + escapeHtml(exif.iso));
            if (exif.exposure) settings.push(escapeHtml(exif.exposure));
            if (exif.fstop) settings.push(escapeHtml(exif.fstop));
            if (exif.focal) settings.push(escapeHtml(exif.focal));
            
            if (settings.length > 0) {
                exifItems.innerHTML += '<div class="viewer-exif-item"><span class="viewer-exif-label">Settings:</span> <span class="viewer-exif-value">' + settings.join(' • ') + '</span></div>';
                hasExif = true;
            }

            // Add GPS
            if (exif.gps) {
                const gpsUrl = getGpsUrl(exif.gps.lat, exif.gps.lon);
                exifItems.innerHTML += '<div class="viewer-exif-item viewer-exif-gps"><span class="viewer-exif-label">Location:</span> <a href="' + gpsUrl + '" target="_blank" class="viewer-gps-link">' + escapeHtml(exif.gps.coords) + '</a></div>';
                hasExif = true;
            }

            exifSection.style.display = hasExif ? 'block' : 'none';
        }

        // Show viewer
        mediaViewer.classList.add('active');
        viewerOpen = true;

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    /**
     * Generate GPS URL based on configured provider
     * @param {number} lat - Latitude
     * @param {number} lon - Longitude
     * @returns {string} URL to open in map provider
     */
    function getGpsUrl(lat, lon) {
        if (config.mapProvider === 'googlemaps') {
            return 'https://www.google.com/maps/search/' + lat + ',' + lon + '/@' + lat + ',' + lon + ',12z';
        } else {
            // Default to OpenStreetMap
            return 'https://www.openstreetmap.org/?mlat=' + lat + '&mlon=' + lon + '&zoom=12&layers=M';
        }
    }

    /**
     * Close media viewer
     */
    function closeMediaViewer() {
        const mediaViewer = document.getElementById('media-viewer');
        if (mediaViewer) {
            mediaViewer.classList.remove('active');
        }
        viewerOpen = false;
        document.body.style.overflow = '';
    }

    /**
     * Navigate to next media in viewer
     */
    function viewerNext() {
        if (viewerCurrentIndex < viewerMediaData.length - 1) {
            openMediaViewerAtIndex(viewerCurrentIndex + 1);
        }
    }

    /**
     * Navigate to previous media in viewer
     */
    function viewerPrevious() {
        if (viewerCurrentIndex > 0) {
            openMediaViewerAtIndex(viewerCurrentIndex - 1);
        }
    }

    /**
     * Setup resize observer to handle responsive layout
     */
    function setupResizeObserver() {
        if ('ResizeObserver' in window) {
            const container = document.querySelector('.photobook-container');
            if (container) {
                const resizeObserver = new ResizeObserver(function() {
                    // Re-layout pages if needed
                    if (pages[currentPage]) {
                        pages[currentPage].scrollIntoView({ behavior: 'auto', block: 'start' });
                    }
                });
                resizeObserver.observe(container);
            }
        }
    }

    /**
     * Export public API for configuration
     */
    window.Photobook = {
        setPhotosPerPage: function(num) {
            config.photosPerPage = num;
        },
        goToPage: function(pageNum) {
            if (pageNum > 0 && pageNum <= pages.length) {
                showPage(pageNum - 1);
            }
        },
        nextPage: nextPage,
        previousPage: previousPage,
        getCurrentPage: function() {
            return currentPage + 1;
        },
        getTotalPages: function() {
            return pages.length;
        },
        setMapProvider: function(provider) {
            if (provider === 'googlemaps' || provider === 'openstreetmap') {
                config.mapProvider = provider;
                // Re-setup GPS links with new provider
                setupGpsLinks();
            }
        },
        getMapProvider: function() {
            return config.mapProvider;
        }
    };

    // Initialize when DOM is ready
    // Use multiple approaches to ensure init() runs on all browsers including Android
    if (document.readyState === 'loading') {
        // DOM is still loading
        document.addEventListener('DOMContentLoaded', function() {
            init();
            setupResizeObserver();
        });
    } else if (document.readyState === 'interactive') {
        // DOM is interactive but resources might still be loading
        // Schedule immediately
        setTimeout(function() {
            init();
            setupResizeObserver();
        }, 0);
    } else {
        // DOM is complete
        init();
        setupResizeObserver();
    }

    // Fallback: ensure init runs even if above conditions don't
    document.addEventListener('DOMContentLoaded', function() {
        // Re-run setup to catch any elements that might have been missed
        setupMediaViewer();
        setupOutlineNavigation();
    });

})();
