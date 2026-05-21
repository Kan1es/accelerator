
const CONFIG = {
    REDIRECT: {
        employee: 'employee_dashboard.html',
        manager:  'manager_dashboard.html',
    },

    ROLE_LABELS: {
        employee: 'Сотрудник',
        manager:  'Управляющий',
    }
};


let selectedRole = null;

document.addEventListener('DOMContentLoaded', () => {
    const text   = 'Здравствуйте, выберите свою роль';
    const target = document.getElementById('tw-role');
    let i = 0;

    function type() {
        if (i < text.length) {
            target.innerHTML += text.charAt(i++);
            setTimeout(type, 60);
        }
    }
    type();
    bindArrows('card-emp', 'arrow-to-emp');
    bindArrows('card-mgr', 'arrow-to-mgr');
});

function bindArrows(cardId, arrowId) {
    const card  = document.getElementById(cardId);
    const arrow = document.getElementById(arrowId);
    if (!card || !arrow) return;

    card.addEventListener('mouseenter', () => {
        arrow.style.color  = '#FF9A3C';
        arrow.style.filter = 'drop-shadow(0 0 8px rgba(255,154,60,0.5))';
    });
    card.addEventListener('mouseleave', () => {
        arrow.style.color  = '#2A2A2A';
        arrow.style.filter = 'none';
    });
}

function selectRole(role) {
    selectedRole = role;
    ['card-emp', 'card-mgr'].forEach(id => {
        document.getElementById(id).classList.remove('selected');
    });
    const cardMap = { employee: 'card-emp', manager: 'card-mgr' };
    document.getElementById(cardMap[role]).classList.add('selected');

    document.getElementById('role-label').textContent = CONFIG.ROLE_LABELS[role];

    document.getElementById('role-icon-emp').classList.add('hidden');
    document.getElementById('role-icon-mgr').classList.add('hidden');
    const iconMap = { employee: 'role-icon-emp', manager: 'role-icon-mgr' };
    document.getElementById(iconMap[role]).classList.remove('hidden');

    const section = document.getElementById('login-section');
    section.classList.add('open');

    setTimeout(() => {
        document.getElementById('input-login').focus();
    }, 400);

    clearError();
}

function resetRole() {
    selectedRole = null;

    ['card-emp', 'card-mgr'].forEach(id => {
        document.getElementById(id).classList.remove('selected');
    });

    const section = document.getElementById('login-section');
    section.classList.remove('open');

    clearError();
    document.getElementById('login-form').reset();
}

function togglePassword() {
    const input  = document.getElementById('input-password');
    const icon   = document.getElementById('eye-icon');
    const isHide = input.type === 'password';

    input.type = isHide ? 'text' : 'password';

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

    if (!selectedRole) {
        showError('Сначала выберите роль');
        return;
    }

    const login    = document.getElementById('input-login').value.trim();
    const password = document.getElementById('input-password').value;

    if (!login)    { showError('Введите логин');  return; }
    if (!password) { showError('Введите пароль'); return; }

    setLoading(true);
    try {
        const data = await window.api.login(login, password, selectedRole);
        window.location.href = CONFIG.REDIRECT[data.role] || CONFIG.REDIRECT.employee;
    } catch (err) {
        if (err.isTimeout)       showError('Сервер не отвечает');
        else if (err.isNetwork)  showError('Ошибка соединения с сервером');
        else if (err.status === 401) showError('Неверный логин или пароль');
        else if (err.status === 403) showError(err.message || 'Роль не совпадает');
        else                     showError(err.message || 'Ошибка входа');
    } finally {
        setLoading(false);
    }
});