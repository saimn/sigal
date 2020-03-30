/*
 * copyright (c) 2020 Bowen Ding
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
*/

"use strict"
class Decryptor {
    constructor(config) {
        const c = Decryptor._getCrypto();
        if (Decryptor.isWorker()) {
            this._role = "worker";
            const encoder = new TextEncoder("utf-8");
            const salt = encoder.encode(config.kdf_salt);
            const iters = config.kdf_iters;
            const shared_key = encoder.encode(config.password);
            const gcm_tag = encoder.encode(config.gcm_tag);

            Decryptor
            ._initAesKey(c, salt, iters, shared_key)
            .then((aes_key) => {
                this._decrypt = (encrypted_blob_arraybuffer) => 
                    Decryptor.decrypt(c, encrypted_blob_arraybuffer,
                        aes_key, gcm_tag);
            })
            .then(() => {
                Decryptor._sendEvent(self, "DecryptWorkerReady");
            });
        } else {
            this._role = "main";
            this._jobCount = 0;
            this._numWorkers = Math.min(4, navigator.hardwareConcurrency);
            this._jobMap = new Map();
            this._workerReady = false;
            this._galleryId = config.galleryId;
            Decryptor._initPage();
            if (!("password" in config && config.password)) {
                this._askPassword()
                .then((password) => {
                    config.password = password;
                    this._createWorkerPool(config);
                })
            } else {
                this._createWorkerPool(config);
            }
        }

        console.info("Decryptor initialized");
    }

    /* main thread only */
    static init(config) {
        if (Decryptor.isWorker()) return;
        window.decryptor = new Decryptor(config);
    }

    static isWorker() {
        return ('undefined' !== typeof WorkerGlobalScope) && ("function" === typeof importScripts) && (navigator instanceof WorkerNavigator);
    }

    static _getCrypto() {
        if(crypto && crypto.subtle) {
            return crypto.subtle;
        } else {
            throw new Error("Fatal: Browser does not support Web Crypto");
        }
    }

    /* main thread only */
    async _askPassword() {
        let password = sessionStorage.getItem(this._galleryId);
        if (!password) {
            return new Promise((s, e) => {
                window.addEventListener(
                    "load",
                    s,
                    { once: true, passive: true }
                );
            }).then((e) => {
                const password = prompt("Input password to view this gallery:");
                if (password) {
                    sessionStorage.setItem(this._galleryId, password);
                    return password;
                } else {
                    return "__wrong_password__";
                }
            });
        } else {
            return password;
        }
    }

    static async _initAesKey(crypto, kdf_salt, kdf_iters, shared_key) {
        const pbkdf2key = await crypto.importKey(
            "raw", 
            shared_key, 
            "PBKDF2", 
            false, 
            ["deriveKey"]
        );
        const pbkdf2params = {
            name: "PBKDF2",
            hash: "SHA-1",
            salt: kdf_salt,
            iterations: kdf_iters
        };
        return await crypto.deriveKey(
            pbkdf2params, 
            pbkdf2key, 
            { name: "AES-GCM", length: 128 }, 
            false, 
            ["decrypt"]
        );
    }

    async _doReload(url, img) {
        const proceed = Decryptor._sendEvent(img, "DecryptImageBeforeLoad", {oldSrc: url});
        if (proceed) {
            let old_src = url;
            try {
                const blobUrl = await this.dispatchJob("reloadImage", [old_src, null]);
                img.addEventListener(
                    "load", 
                    (e) => Decryptor._sendEvent(e.target, "DecryptImageLoaded", {oldSrc: old_src}),
                    {once: true, passive: true}
                );
                img.src = blobUrl;
            } catch (error) {
                img.addEventListener(
                    "load", 
                    (e) => Decryptor._sendEvent(e.target, "DecryptImageError", {oldSrc: old_src, error: error}),
                    {once: true, passive: true}
                );
                img.src = Decryptor.imagePlaceholderURL;
                // password is incorrect
                if (error.message.indexOf("decryption failed") >= 0) {
                    sessionStorage.removeItem(this._galleryId);
                }
                throw new Error(`Image reload failed: ${error.message}`);
            }
        }
    }
    
    async reloadImage(url, img) {
        if (this._role === "main") {
            const full_url = (new URL(url, window.location)).toString();
            if (!this.isWorkerReady()) {
                document.addEventListener(
                    "DecryptWorkerReady",
                    (e) => { this._doReload(full_url, img); },
                    {once: true, passive: true}
                );
            } else {
                this._doReload(full_url, img);
            }
        } else if (this._role === "worker") {
            let r;
            try {
                r = await fetch(url);
            } catch (e) {
                throw new Error("fetch failed");
            }
            if (r && r.ok) {
                const encrypted_blob = await r.blob();
                try {
                    const decrypted_blob = await this._decrypt(encrypted_blob);
                    return URL.createObjectURL(decrypted_blob);
                } catch (e) {
                    throw new Error(`decryption failed: ${e.message}`);
                }
            } else {
                throw new Error("fetch failed");
            }
        }
    }

    /* main thread only */
    static onNewImageError(e) {
        if (e.target.src.startsWith("blob")) return;
        if (!window.decryptor) return;

        window.decryptor.reloadImage(e.target.src, e.target);
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
    }

    static _sendEvent(target, type, detail = null) {
        const eventInit = {
            detail: detail,
            bubbles: true,
            cancelable: true
        };
        return target.dispatchEvent(new CustomEvent(type, eventInit));
    }

    /* main thread only */
    static _initPage() {
        document.addEventListener(
            "error",
            e => {
                if (e.target instanceof HTMLImageElement) {
                    Decryptor.onNewImageError(e);
                }
            },
            {capture: true}
        );

        Image = (function (oldImage) {
            function Image(...args) {
                let img = new oldImage(...args);
                img.addEventListener(
                    "error",
                    Decryptor.onNewImageError
                );
                return img;
            }
            Image.prototype = oldImage.prototype;
            Image.prototype.constructor = Image;
            return Image;
        })(Image);

        document.createElement = (function(create) {
            return function() {
                let ret = create.apply(this, arguments);
                if (ret.tagName.toLowerCase() === "img") {
                    ret.addEventListener(
                        "error",
                        Decryptor.onNewImageError
                    );
                }
                return ret;
            };
        })(document.createElement);
    }

    static async decrypt(crypto, blob, aes_key, gcm_tag) {
        const iv = await blob.slice(0, 12).arrayBuffer();
        const ciphertext = await blob.slice(12).arrayBuffer();
        const decrypted = await crypto.decrypt(
                {
                    name: "AES-GCM",
                    iv: iv,
                    additionalData: gcm_tag
                },
                aes_key,
                ciphertext
            );
        return new Blob([decrypted], {type: blob.type});
    }

    isWorkerReady() {
        return this._workerReady;
    }

    _createWorkerPool(config) {
        if (this._role !== "main") return;
        if (this._workerReady) return;

        let callback = (e) => {
            const callbacks = this._jobMap.get(e.data.id);
            if (e.data.success) {
                if (callbacks.success) callbacks.success(e.data.result);
            } else {
                if (callbacks.error) callbacks.error(new Error(e.data.result));
            }
            this._jobMap.delete(e.data.id);
        };

        let pool = Array();
        
        for (let i = 0; i < this._numWorkers; i++) {
            let worker = new Worker(config.worker_script);
            worker.onmessage = callback;
            pool.push(worker);
        }
        this._workerPool = pool;

        let notReadyWorkers = this._numWorkers;
        for (let i = 0; i < this._numWorkers; i++) {
            this.dispatchJob("new", [config])
            .then(() => { 
                if (--notReadyWorkers <= 0) {
                    this._workerReady = true;
                    Decryptor._sendEvent(document, "DecryptWorkerReady");
                }
            });
        }
    }

    /*
     * method: string
     * args: Array
     */
    dispatchJob(method, args) {
        if (this._role === "main") {
            return new Promise((success, error) => {
                const jobId = this._jobCount++;
                const worker = this._workerPool[jobId % this._numWorkers];
                this._jobMap.set(jobId, {success: success, error: error});
                Decryptor._postJobToWorker(jobId, worker, method, args);
            });
        } else if (this._role === "worker") {
            return Decryptor._asyncReturn(this, method, args)
            .then(
                (result) => { return {success: true, result: result}; }, 
                (error) => { return {success: false, result: error.message}; }
            );
        }
    }

    static _asyncReturn(instance, method, args) {
        if (method in instance && instance[method] instanceof Function) {
            try {
                let promise_or_value = instance[method].apply(instance, args);
                if (promise_or_value instanceof Promise) {
                    return promise_or_value;
                } else {
                    return Promise.resolve(promise_or_value);
                }
            } catch (e) {
                return Promise.reject(e);
            }
        } else {
            return Promise.reject(new Error(`no such method: ${method}`))
        }
    }

    static _postJobToWorker(jobId, worker, method, args) {
        const job = {
            id: jobId,
            method: method,
            args: args
        };
        worker.postMessage(job);
    }

    /* worker thread only */
    static onWorkerMessage(e) {
        const id = e.data.id;
        const method = e.data.method;
        const args = e.data.args;

        if (method === "new") {
            self.decryptor = new Decryptor(...args);
            self.addEventListener(
                "DecryptWorkerReady",
                (e) => self.postMessage({id: id, success: true, result: "worker ready"}),
                {once: true, passive: true}
            );
        } else {
            self.decryptor
            .dispatchJob(method, args)
            .then((reply) => {
                reply.id = id;
                self.postMessage(reply);
            });
        }
    }
}

Decryptor.imagePlaceholderURL = URL.createObjectURL(new Blob([
`<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
<!-- Created with Method Draw - http://github.com/duopixel/Method-Draw/ -->
<g>
 <title>background</title>
 <rect fill="#ffffff" id="canvas_background" height="202" width="202" y="-1" x="-1"/>
 <g display="none" overflow="visible" y="0" x="0" height="100%" width="100%" id="canvasGrid">
  <rect fill="url(#gridpattern)" stroke-width="0" y="0" x="0" height="100%" width="100%"/>
 </g>
</g>
<g>
 <title>Layer 1</title>
 <text xml:space="preserve" text-anchor="start" font-family="Helvetica, Arial, sans-serif" font-size="36" id="svg_1" y="61.949997" x="22.958336" stroke-width="0" stroke="#000" fill="#7f7f7f">Could not</text>
 <text xml:space="preserve" text-anchor="start" font-family="Helvetica, Arial, sans-serif" font-size="36" id="svg_4" y="112.600002" x="65.974998" stroke-width="0" stroke="#000" fill="#7f7f7f">load</text>
 <text xml:space="preserve" text-anchor="start" font-family="Helvetica, Arial, sans-serif" font-size="36" id="svg_5" y="162.949997" x="50.983334" stroke-width="0" stroke="#000" fill="#7f7f7f">image</text>
</g>
</svg>`], {type: "image/svg+xml"}));

