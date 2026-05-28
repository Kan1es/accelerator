/**
 * ws.js — WebSocket client for real-time notifications.
 *
 * Connects to  ws[s]://<host>/ws/notifications/?token=<DRF-token>
 * On each incoming message dispatches two CustomEvents on window:
 *   'ws:<type>'   — e.g. 'ws:ticket_assigned', 'ws:ticket_status_changed'
 *   'ws:message'  — fires for every message (catch-all)
 *
 * Exposes window.WS = { connect(), disconnect(), isConnected() }
 *
 * Auto-connects at script execution if a token is already present.
 * Reconnects automatically with exponential back-off on unexpected close.
 */
(function () {
    'use strict';

    /** Back-off delays in ms: 1s → 2s → 5s → 10s → 30s (stays at 30s) */
    var BACKOFF = [1000, 2000, 5000, 10000, 30000];

    var _ws             = null;
    var _attempt        = 0;
    var _reconnectTimer = null;
    var _intentional    = false;

    // ── Helpers ──────────────────────────────────────────────────────────────

    function _token() {
        return (window.api && typeof window.api.getToken === 'function')
            ? window.api.getToken()
            : null;
    }

    function _wsUrl() {
        var tok = _token();
        if (!tok) return null;
        var proto = (location.protocol === 'https:') ? 'wss:' : 'ws:';
        return proto + '//' + location.host + '/ws/notifications/?token=' + encodeURIComponent(tok);
    }

    function _dispatch(name, detail) {
        try {
            window.dispatchEvent(new CustomEvent(name, { detail: detail }));
        } catch (_) {}
    }

    // ── Core ─────────────────────────────────────────────────────────────────

    function connect() {
        if (_ws && (_ws.readyState === 0 /* CONNECTING */ ||
                    _ws.readyState === 1 /* OPEN */)) return;

        var url = _wsUrl();
        if (!url) return; // no auth token yet — caller responsible for retry

        _intentional = false;

        try {
            _ws = new WebSocket(url);
        } catch (_) {
            _scheduleReconnect();
            return;
        }

        _ws.onopen = function () {
            _attempt = 0;
            _dispatch('ws:connected', {});
        };

        _ws.onmessage = function (evt) {
            var data;
            try { data = JSON.parse(evt.data); } catch (_) { return; }
            var type = data.type || 'unknown';
            _dispatch('ws:' + type, data);
            _dispatch('ws:message', data);
        };

        _ws.onclose = function () {
            _ws = null;
            _dispatch('ws:disconnected', {});
            if (!_intentional) _scheduleReconnect();
        };

        _ws.onerror = function () {
            /* onclose fires right after — reconnect logic lives there */
        };
    }

    function disconnect() {
        _intentional = true;
        if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
        if (_ws) { try { _ws.close(); } catch (_) {} _ws = null; }
    }

    function isConnected() {
        return _ws !== null && _ws.readyState === 1 /* OPEN */;
    }

    function _scheduleReconnect() {
        var delay = BACKOFF[Math.min(_attempt, BACKOFF.length - 1)];
        _attempt++;
        _reconnectTimer = setTimeout(connect, delay);
    }

    // ── Public API ────────────────────────────────────────────────────────────

    window.WS = { connect: connect, disconnect: disconnect, isConnected: isConnected };

    // Auto-connect: defer one tick so api.js finishes initialising first.
    setTimeout(function () {
        if (_token()) connect();
    }, 0);
})();
