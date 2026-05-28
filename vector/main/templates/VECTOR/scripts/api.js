// Общая утилита фронта для запросов к Django-бэку.
// Подключайте перед основными скриптами:
//   <script src="scripts/api.js"></script>
//
// Использование:
//   const data = await api.get('/api/employee/status/');
//   await api.post('/api/auth/login/', { login, password });
//
// 401 -> редирект на /login.html, токен очищается.

window.api = (function () {
    const STORAGE_KEYS = {
        token: 'auth_token',
        role: 'user_role',
        name: 'user_name',
        login: 'user_login',
        employeeId: 'employee_id',
    };

    function getToken() {
        return localStorage.getItem(STORAGE_KEYS.token);
    }

    function setSession({ token, role, name, login, employee_id }) {
        if (token) localStorage.setItem(STORAGE_KEYS.token, token);
        if (role) localStorage.setItem(STORAGE_KEYS.role, role);
        if (name) localStorage.setItem(STORAGE_KEYS.name, name);
        if (login) localStorage.setItem(STORAGE_KEYS.login, login);
        if (employee_id !== undefined) localStorage.setItem(STORAGE_KEYS.employeeId, String(employee_id));
    }

    function clearSession() {
        Object.values(STORAGE_KEYS).forEach((k) => localStorage.removeItem(k));
    }

    function getSession() {
        return {
            token: localStorage.getItem(STORAGE_KEYS.token),
            role: localStorage.getItem(STORAGE_KEYS.role),
            name: localStorage.getItem(STORAGE_KEYS.name),
            login: localStorage.getItem(STORAGE_KEYS.login),
            employeeId: localStorage.getItem(STORAGE_KEYS.employeeId),
        };
    }

    function dashboardHref(role) {
        return role === 'manager' ? '/manager_dashboard.html' : '/employee_dashboard.html';
    }

    function initAuthChrome() {
        const session = getSession();
        if (!session.token) return;
        const loginLink = document.querySelector('a[href="login.html"], a[href="/login.html"]');
        if (loginLink) {
            loginLink.href = dashboardHref(session.role);
            loginLink.textContent = 'Кабинет';
        }
    }

    async function request(method, url, body, { auth = true, timeoutMs = 15000 } = {}) {
        const headers = { 'Accept': 'application/json' };
        if (body !== undefined && body !== null) {
            headers['Content-Type'] = 'application/json';
        }
        if (auth) {
            const token = getToken();
            if (token) headers['Authorization'] = `Token ${token}`;
        }

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);

        let resp;
        try {
            resp = await fetch(url, {
                method,
                headers,
                body: body !== undefined && body !== null ? JSON.stringify(body) : undefined,
                signal: controller.signal,
            });
        } catch (err) {
            clearTimeout(timer);
            const isAbort = err.name === 'AbortError';
            throw {
                status: 0,
                isNetwork: !isAbort,
                isTimeout: isAbort,
                message: isAbort ? 'Превышено время ожидания' : 'Ошибка сети',
            };
        }
        clearTimeout(timer);

        if (resp.status === 401) {
            clearSession();
            // Если уже на login.html — не редиректим, отдадим ошибку.
            if (!location.pathname.endsWith('/login.html')) {
                location.href = '/login.html';
            }
        }

        let data = null;
        const ct = resp.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
            try { data = await resp.json(); } catch { /* пусто */ }
        } else {
            try { data = await resp.text(); } catch { /* пусто */ }
        }

        if (!resp.ok) {
            throw {
                status: resp.status,
                data,
                message: (data && data.error) || `HTTP ${resp.status}`,
            };
        }
        return data;
    }

    return {
        get: (url, opts) => request('GET', url, null, opts),
        post: (url, body, opts) => request('POST', url, body, opts),
        patch: (url, body, opts) => request('PATCH', url, body, opts),
        del: (url, opts) => request('DELETE', url, null, opts),

        getToken,
        getSession,
        setSession,
        clearSession,
        dashboardHref,
        initAuthChrome,

        async login(loginVal, password, role) {
            const data = await this.post('/api/auth/login/',
                { login: loginVal, password, role },
                { auth: false });
            this.setSession(data);
            return data;
        },

        async logout() {
            try { await this.post('/api/auth/logout/', {}); } catch { /* всё равно чистим */ }
            this.clearSession();
            location.href = '/login.html';
        },

        requireAuth() {
            if (!getToken()) {
                location.href = '/login.html';
                return false;
            }
            return true;
        },
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    window.api?.initAuthChrome?.();
});
