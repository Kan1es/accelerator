const REDIRECT = {
    employee: 'employee_dashboard.html',
    manager:  'manager_dashboard.html',
};

document.addEventListener('DOMContentLoaded', () => {
    // Если уже залогинен — сразу на дашборд
    const session = window.api?.getSession?.();
    if (session?.token) {
        window.location.href = REDIRECT[session.role] || REDIRECT.employee;
        return;
    }
    document.getElementById('input-login')?.focus();
});

function togglePassword() {
    const input  = document.getElementById('input-password');
    const icon   = document.getElementById('eye-icon');
    const isHide = input.type === 'password';
    input.type   = isHide ? 'text' : 'password';
    icon.innerHTML = isHide
        ? `<path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
           <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
           <line x1="1" y1="1" x2="23" y2="23"/>`
        : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
           <circle cx="12" cy="12" r="3"/>`;
}

function showError(msg) {
    const box = document.getElementById('error-box');
    box.textContent = msg;
    box.classList.add('show');
    document.getElementById('input-login').classList.add('error');
    document.getElementById('input-password').classList.add('error');
}

function clearError() {
    document.getElementById('error-box').classList.remove('show');
    document.getElementById('input-login')?.classList.remove('error');
    document.getElementById('input-password')?.classList.remove('error');
}

function setLoading(state) {
    const btn     = document.getElementById('submit-btn');
    const text    = document.getElementById('btn-text');
    const spinner = document.getElementById('btn-spinner');
    btn.disabled  = state;
    text.classList.toggle('hidden', state);
    spinner.classList.toggle('hidden', !state);
}

['input-login', 'input-password'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', clearError);
});

document.getElementById('login-form').addEventListener('submit', async e => {
    e.preventDefault();
    clearError();

    const login    = document.getElementById('input-login').value.trim();
    const password = document.getElementById('input-password').value;

    if (!login)    { showError('Введите логин');  return; }
    if (!password) { showError('Введите пароль'); return; }

    setLoading(true);
    try {
        // Роль не передаём — бэкенд определяет сам по данным сотрудника
        const data = await window.api.login(login, password);
        window.location.href = REDIRECT[data.role] || REDIRECT.employee;
    } catch (err) {
        if (err.isTimeout)        showError('Сервер не отвечает, попробуйте позже');
        else if (err.isNetwork)   showError('Ошибка соединения с сервером');
        else if (err.status === 401) showError('Неверный логин или пароль');
        else                      showError(err.message || 'Ошибка входа');
    } finally {
        setLoading(false);
    }
});
