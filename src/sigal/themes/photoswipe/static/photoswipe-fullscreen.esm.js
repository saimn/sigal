/**
 * PhotoSwipe fullscreen plugin v1.0.5
 *
 * Inspired by https://github.com/dimsemenov/PhotoSwipe/issues/1759
 *
 * By https://arnowelzel.de
 */

const defaultOptions = {
    fullscreenTitle: 'Toggle fullscreen'
};

class PhotoSwipeFullscreen {
    constructor(lightbox, options) {
        this.options = {
            ...defaultOptions,
            ...options
        };
        this.lightbox = lightbox;
        this.lightbox.on('init', () => {
            this.initPlugin(this.lightbox.pswp);
        });
    }

    initPlugin(pswp) {
        this.fullscreenAPI = this.getFullscreenAPI();
        const fullscreenSVG = '<svg aria-hidden="true" class="pswp__icn" viewBox="0 0 32 32" width="32" height="32">' +
            '<use class="pswp__icn-shadow" xlink:href="#pswp__icn-fullscreen-exit"/>' +
            '<use class="pswp__icn-shadow" xlink:href="#pswp__icn-fullscreen-request"/>' +
            '<path id="pswp__icn-fullscreen-request" transform="translate(4,4)" d="M20 3h2v6h-2V5h-4V3h4zM4 3h4v2H4v4H2V3h2zm16 16v-4h2v6h-6v-2h4zM4 19h4v2H2v-6h2v4z" /></g>' +
            '<path id="pswp__icn-fullscreen-exit" style="display:none" transform="translate(4,4)" d="M18 7h4v2h-6V3h2v4zM8 9H2V7h4V3h2v6zm10 8v4h-2v-6h6v2h-4zM8 15v6H6v-4H2v-2h6z"/>' +
            '</svg>';

        if (this.fullscreenAPI) {
            pswp.on('uiRegister', () => {
                pswp.ui.registerElement({
                    name: 'fullscreen-button',
                    title: this.options.fullscreenTitle,
                    order: 9,
                    isButton: true,
                    html: fullscreenSVG,
                    onClick: (event, el) => {
                        this.toggleFullscreen();
                    }
                });

                pswp.events.add(document, 'keydown', (e) => {
                    if (e.keyCode == 70) { // 'f'
                        this.toggleFullscreen();
                        e.preventDefault();
                    }
                });
            });
        }

        this.lightbox.on('close', () => {
            if (this.fullscreenAPI && this.fullscreenAPI.isFullscreen()) {
                this.fullscreenAPI.exit();
            }
        });
    }

    toggleFullscreen() {
        if (this.fullscreenAPI) {
            if (this.fullscreenAPI.isFullscreen()) {
                // Exit full-screen mode
                this.fullscreenAPI.exit();
                // Toggle "Exit" and "Enter" full-screen SVG icon display
                setTimeout(function() {
                    document.getElementById('pswp__icn-fullscreen-exit').style.display = 'none';
                    document.getElementById('pswp__icn-fullscreen-request').style.display = 'inline';
                }, 300);
            } else {
                // Enter full-screen mode
                this.fullscreenAPI.request(document.querySelector(`.pswp`));
                // Toggle "Exit" and "Enter" full-screen SVG icon display
                setTimeout(function() {
                    document.getElementById('pswp__icn-fullscreen-exit').style.display = 'inline';
                    document.getElementById('pswp__icn-fullscreen-request').style.display = 'none';
                }, 300);
            }
        }
    }

    getFullscreenAPI() {
        let api;
        let enterFS;
        let exitFS;
        let elementFS;
        let changeEvent;
        let errorEvent;

        if (document.fullscreenEnabled) {
            enterFS = 'requestFullscreen';
            exitFS = 'exitFullscreen';
            elementFS = 'fullscreenElement';
            changeEvent = 'fullscreenchange';
            errorEvent = 'fullscreenerror';
        } else if (document.webkitFullscreenEnabled) {
            enterFS = 'webkitRequestFullscreen';
            exitFS = 'webkitExitFullscreen';
            elementFS = 'webkitFullscreenElement';
            changeEvent = 'webkitfullscreenchange';
            errorEvent = 'webkitfullscreenerror';
        }
        if (enterFS) {
            api = {
                request: function (el) {
                    if (enterFS === 'webkitRequestFullscreen') {
                        el[enterFS](Element.ALLOW_KEYBOARD_INPUT);
                    } else {
                        el[enterFS]();
                    }
                },
                exit: function () {
                    return document[exitFS]();
                },
                isFullscreen: function () {
                    return document[elementFS];
                },
                change: changeEvent,
                error: errorEvent
            };
        }
        return api;
    }
}

export default PhotoSwipeFullscreen;
