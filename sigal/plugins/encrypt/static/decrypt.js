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
        this._jobCount = 0;
        this._jobMap = new Map();
        this._workerReady = false;

        if (Decryptor.isServiceWorker()) {
            this._role = "service_worker";
        } else if (!Decryptor.isWorker()) {
            if (!Decryptor.featureTest()) {
                alert("This page cannot function properly because your browser does not support some critical features or you are in private browsing mode. Please update your browser or exit private browsing mode.");
                return;
            }
            this._role = "main";
            this._config = config;
            const local_config = this._mGetLocalConfig();
            if (local_config) {
                this._config = local_config;
            }
            window.addEventListener(
                "load",
                (e) => this._mSetupServiceWorker(),
                { once: true, passive: true }
            );
        }

        console.info("Decryptor initialized");
    }

    static init(config) {
        if (Decryptor.isServiceWorker()) {
            self.decryptor = new Decryptor(config);
        } else {
            window.decryptor = new Decryptor(config);
        }
    }

    static featureTest() {
        let features = [
            typeof crypto,
            typeof TextEncoder,
            typeof navigator.serviceWorker,
            typeof Proxy,
            typeof fetch,
            typeof Blob.prototype.arrayBuffer,
            typeof Response.prototype.clone,
            typeof caches
        ];
        return features.every((e) => e !== "undefined");
    }

    async _swInitServiceWorker(config) {
        const crypto = Decryptor._getCrypto();
        const encoder = new TextEncoder("utf-8");
        const salt = encoder.encode(config.kdf_salt);
        const iters = config.kdf_iters;
        const shared_key = encoder.encode(config.password);
        const gcm_tag = encoder.encode(config.gcm_tag);

        const aes_key = await Decryptor._initAesKey(crypto, salt, iters, shared_key);
        if (await this._swCheckAesKey(aes_key, gcm_tag)) {
            this.workerReady = true;
            this._decrypt = (encrypted_blob_arraybuffer) => 
                Decryptor.decrypt(crypto, encrypted_blob_arraybuffer, aes_key, gcm_tag);
            this._swNotifyWorkerReady();
        } else {
            this.workerReady = false;
            this._swNotifyIncorrectPassword()
        }
    }

    async _swCheckAesKey(aes_key, gcm_tag) {
        let response;
        try {
            response = await fetch(Decryptor.keyCheckURL);
        } catch (error) {
            throw new Error("Fetched failed when checking encryption key");
        }
        try {
            await Decryptor.decrypt(
                Decryptor._getCrypto(),
                await response.blob(),
                aes_key,
                gcm_tag,
                true
            );
        } catch (error) {
            console.warn("Password is incorrect!");
            return false;
        }
        return true;
    }

    async _swNotifyWorkerReady() {
        const array_clients = await self.clients.matchAll({includeUncontrolled: true});
        for (let client of array_clients) {
            this._proxyWrap(client)._mSetWorkerReady();
        }
    }

    async _swNotifyIncorrectPassword() {
        const array_clients = await self.clients.matchAll({includeUncontrolled: true});
        for (let client of array_clients) {
            this._proxyWrap(client)._mUnsetWorkerReady();
        }
    }

    static isInitialized() {
        if (Decryptor.isServiceWorker()) {
            return 'decryptor' in self && self.decryptor.workerReady;
        } else {
            return 'decryptor' in window && window.decryptor.workerReady;
        }
    }

    get workerReady() {
        return this._workerReady;
    }

    set workerReady(val) {
        this._workerReady = (val ? true : false);
        if (this._workerReady) {
            const eventTarget = (Decryptor.isWorker() ? self : document);
            Decryptor._sendEvent(eventTarget, "DecryptWorkerReady");
        }
    }

    _mSetWorkerReady() {
        this.workerReady = true;
        const had_been_ready_before = localStorage.getItem(this._config.galleryId) !== null;
        localStorage.setItem(this._config.galleryId, JSON.stringify(this._config));
        if (!had_been_ready_before) {
            window.location.reload();
        }
    }

    _mUnsetWorkerReady() {
        this.workerReady = false;
        localStorage.removeItem(this._config.galleryId);
    }

    _mGetLocalConfig() {
        const local_config = JSON.parse(localStorage.getItem(this._config.galleryId));
        if (local_config 
            && local_config.galleryId
            && local_config.sw_script
            && local_config.password
            && local_config.gcm_tag
            && local_config.kdf_salt
            && local_config.kdf_iters) {
            return local_config;
        } else {
            return null;
        }
    }

    async _mSetupServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.error("Fatal: Your browser does not support service worker");
            throw new Error("no service worker support");
        }

        if (navigator.serviceWorker.controller) {
            this.serviceWorker = navigator.serviceWorker.controller;
        } else {
            navigator.serviceWorker.register(this._config.sw_script);
            const registration = await navigator.serviceWorker.ready;
            this.serviceWorker = registration.active;
        }

        navigator.serviceWorker.onmessage = 
            (e) => Decryptor.onMessage(this.serviceWorker, e);
        this.serviceWorker = this._proxyWrap(this.serviceWorker);

        if (!(await this.serviceWorker.Decryptor.isInitialized())) {
            if (!('password' in this._config && this._config.password)) {
                this._config.password = await this._mAskPassword();
            }
            this.serviceWorker._swInitServiceWorker(this._config);
        }
    }

    static isServiceWorker() {
        return ('undefined' !== typeof ServiceWorkerGlobalScope) && ("function" === typeof importScripts) && (navigator instanceof WorkerNavigator);
    }

    static isWorker() {
        return ('undefined' !== typeof WorkerGlobalScope) && ("function" === typeof importScripts) && (navigator instanceof WorkerNavigator);
    }

    static _getCrypto() {
        if('undefined' !== typeof crypto && crypto.subtle) {
            return crypto.subtle;
        } else {
            throw new Error("Fatal: Browser does not support Web Crypto");
        }
    }

    /* main thread only */
    async _mAskPassword() {
        const config = JSON.parse(localStorage.getItem(this._config.galleryId));
        if (config && config.password) {
            return config.password;
        }
        const password = prompt("Input password to view this gallery:");
        if (password) {
            this._config.password = password;
            return password;
        } else {
            return "__wrong_password__";
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

    static _sendEvent(target, type, detail = null) {
        const eventInit = {
            detail: detail,
            bubbles: true,
            cancelable: true
        };
        return target.dispatchEvent(new CustomEvent(type, eventInit));
    }

    static async checkMagicString(arraybuffer) {
        const sample = new DataView(
            arraybuffer, 
            0, 
            Decryptor.MAGIC_STRING_ARRAYBUFFER.byteLength
        );
        for (let i = 0; i < Decryptor.MAGIC_STRING_ARRAYBUFFER.byteLength; i++) {
            if (Decryptor.MAGIC_STRING_ARRAYBUFFER[i] !== sample.getUint8(i)) {
                return false;
            }
        }
        return true;
    }

    static async decrypt(crypto, blob_or_arraybuffer, aes_key, gcm_tag, check_magic_string=false) {
        let arraybuffer, return_blob;
        if (blob_or_arraybuffer instanceof Blob) {
            arraybuffer = await blob_or_arraybuffer.arrayBuffer();
            return_blob = true;
        } else if (blob_or_arraybuffer instanceof ArrayBuffer) {
            arraybuffer = blob_or_arraybuffer
            return_blob = false;
        } else {
            throw new TypeError("decrypt accepts either a Blob or an ArrayBuffer");
        }

        // make sure there is enough data to decrypt
        // although 1 byte of data seems not acceptable for some browsers
        // in which case crypto.decrypt will throw an error
        // "The provided data is too small"
        if (arraybuffer.byteLength < 
            Decryptor.MAGIC_STRING_ARRAYBUFFER.byteLength
            + Decryptor.IV_LENGTH
            + 1) {
            throw new Error("not enough data to decrypt");
        }

        if (check_magic_string && !(await Decryptor.checkMagicString(arraybuffer))) {
            // data is not encrypted
            return blob_or_arraybuffer;
        }
        
        const iv = new DataView(
            arraybuffer, 
            Decryptor.MAGIC_STRING_ARRAYBUFFER.byteLength, 
            Decryptor.IV_LENGTH
        );
        const ciphertext = new DataView(
            arraybuffer, 
            Decryptor.MAGIC_STRING_ARRAYBUFFER.byteLength + Decryptor.IV_LENGTH
        );
        const decrypted = await crypto.decrypt(
            {
                name: "AES-GCM",
                iv: iv,
                additionalData: gcm_tag
            },
            aes_key,
            ciphertext
        );
        if (return_blob) {
            return new Blob([decrypted], {type: blob_or_arraybuffer.type});
        } else {
            return decrypted;
        }
    }

    _proxyWrap(target) {
        const decryptor = this;
        const handler = {
            get: (wrappedObj, prop) => {
                if (prop in wrappedObj) {
                    if (wrappedObj[prop] instanceof Function) {
                        return (...args) => wrappedObj[prop].apply(wrappedObj, args);
                    } else {
                        return wrappedObj[prop];
                    }
                }
                if (prop === "Decryptor") {
                    return new Proxy(target, {
                        get: (wrappedObj, prop) => {
                            return decryptor._rpcCall(wrappedObj, prop, true);
                        }
                    });
                }
                return decryptor._rpcCall(wrappedObj, prop, false);
            }
        }
        return new Proxy(target, handler);
    }

    _rpcCall(target, method, static_) {
        const decryptor = this;
        const dummyFunction = () => {};
        const handler = {
            apply: (wrappedFunc, thisArg, args) => {
                return new Promise((success, error) => {
                    const jobId = decryptor._jobCount++;
                    decryptor._jobMap.set(jobId, {success: success, error: error});
                    Decryptor._rpcPostJob(jobId, target, method, args, static_);
                });
            }
        };
        return new Proxy(dummyFunction, handler);
    }

    static _rpcPostJob(jobId, messagePort, method, args, static_=false) {
        const job = {
            type: "job",
            id: jobId,
            method: method,
            args: args,
            static: static_
        };
        messagePort.postMessage(job);
    }

    static _asyncReturn(instance, method, args) {
        if (!(instance instanceof Object)) {
            return Promise.reject(new Error("calling method on a primitive"));
        }
        if (!(method in instance && instance[method] instanceof Function)) {
            return Promise.reject(new Error(`no such method: ${method}`))
        }
        
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
    }

    static onMessage(replyPort, e) {
        const type = e.data.type;
        const id = e.data.id;

        if (type === "job") {
            const method = e.data.method;
            const args = e.data.args;
            const instance = e.data.static ? Decryptor :
                (Decryptor.isWorker() ? self : window).decryptor;

                Decryptor._asyncReturn(instance, method, args)
            .then(
                (result) => { return {type: "reply", success: true, result: result}; }, 
                (error) => { return {type: "reply", success: false, result: error.message}; }
            )
            .then((reply) => {
                reply.id = id;
                replyPort.postMessage(reply);
            });
        } else if (type === "reply") {
            // if we are receiving replies, we must have been initialized
            // so no need to check if "decryptor" exists here
            const success = e.data.success;
            const result = e.data.result;
            const callbacks = decryptor._jobMap.get(id);

            if (success) {
                if (callbacks.success) callbacks.success(result);
            } else {
                if (callbacks.error) callbacks.error(new Error(result));
            }
            decryptor._jobMap.delete(id);
        }
    }

    static onServiceWorkerInstall(e) {
        console.log("service worker on install: ", e);
        e.waitUntil(self.skipWaiting());
    }

    static onServiceWorkerActivate(e) {
        console.log("service worker on activate: ", e);
        e.waitUntil(self.clients.claim());
    }

    static onServiceWorkerMesssage(e) {
        return Decryptor.onMessage(e.source, e);
    }

    static async _swHandleFetch(e) {
        const request = e.request;
        try {
            const cached_response = await caches.match(request);
            if (cached_response) {
                // TODO: handle cache expiration
                console.debug(`Found cached response for ${request.url}`);
                return cached_response;
            }
        } catch (error) {
            console.error("Caches.match error!");
        }

        let response;
        try {
            response = await fetch(request);
        } catch (error) {
            console.debug(`Fetch failed when trying for ${request.url}: ${error}`);
            throw error;
        }

        if (!response.ok) {
            console.debug(`Fetch succeeded but server returned non-2xx: ${request.url}`);
            return response;
        }

        const is_image = [
            request.destination === "image",
            (() => {
                const content_type = response.headers.get("content-type");
                return content_type && content_type.startsWith("image");
            })()
        ];

        if (!is_image.some((e) => e)) {
            console.debug(`Fetch succeeded but response is likely not an image ${request.url}`);
            return response;
        }

        const response_clone = response.clone();
        const encrypted_blob = await response.blob();
        const encrypted_arraybuffer = await encrypted_blob.arrayBuffer();
        if (!(await Decryptor.checkMagicString(encrypted_arraybuffer))) {
            console.debug(`Response image is not encrypted: ${request.url}`);
            return response_clone;
        }
        console.debug(`Fetch succeeded with encrypted image ${request.url}, trying to decrypt`);

        if (!Decryptor.isInitialized()) {
            if ('decryptor' in self) {
                try{
                    const clients = await self.clients.matchAll({type: "window"});
                    const races = Promise.race(
                        clients.map((client) => {
                            return self.decryptor._proxyWrap(client)._mGetLocalConfig();
                        })
                    );
                    const config = await Promise.timeout(races, 100);
                    await self.decryptor._swInitServiceWorker(config);
                } catch (error) {
                    // do nothing
                }
            }
            if (!Decryptor.isInitialized()) {
                console.debug(`Service worker not initialized on fetch event`);
                return Decryptor.errorResponse.clone();
            }
        }

        let decrypted_blob;
        try {
            decrypted_blob = new Blob(
                [await self.decryptor._decrypt(encrypted_arraybuffer)],
                {type: encrypted_blob.type}
            );
        } catch (error) {
            console.debug(`Decryption failed for ${request.url}: ${error.message}`);
            console.error("Corrupted data??? This shouldn't occur.");
            return Decryptor.errorResponse.clone();
        }

        const decrypted_response = new Response(
            decrypted_blob,
            {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers
            }
        );
        decrypted_response.headers.set("content-length", decrypted_blob.size);
        
        const decrypted_response_clone = decrypted_response.clone();
        const cache = await caches.open("v1");
        cache.put(request, decrypted_response_clone);

        console.debug(`Responding with decrypted response ${request.url}`);
        return decrypted_response;
    }

    static onServiceWorkerFetch(e) {
        e.respondWith(Decryptor._swHandleFetch(e));
    }
}

Decryptor.MAGIC_STRING = "_e_n_c_r_y_p_t_e_d_";
Decryptor.MAGIC_STRING_ARRAYBUFFER = (new TextEncoder("utf-8")).encode(Decryptor.MAGIC_STRING);
Decryptor.IV_LENGTH = 12;
Decryptor.keyCheckURL = "static/keycheck.txt";
Decryptor.imagePlaceholderBlob = new Blob([
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
</svg>`], {type: "image/svg+xml"});

Decryptor.errorResponse = new Response(
    Decryptor.imagePlaceholderBlob,
    {
        status: 200,
        statusText: "OK",
        headers: {
            "content-type": "image/svg+xml"
        }
    }
);

Promise.timeout = function(cb_or_pm, timeout) {
    return Promise.race([
        cb_or_pm instanceof Function ? new Promise(cb) : cb_or_pm,
        new Promise((resolve, reject) => {
            setTimeout(() => {
                reject('Timed out');
            }, timeout);
        })
    ]);
}
