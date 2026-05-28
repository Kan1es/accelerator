document.addEventListener('DOMContentLoaded', () => {

    // ===== ЧАТ (БОКОВАЯ ПАНЕЛЬ) =====
    const toggle = document.getElementById('chat-toggle');
    const body = document.getElementById('chat-body');
    const inputWrap = document.getElementById('chat-input-wrap');
    const chatContainer = document.getElementById('chat');

    if (toggle) {
        let collapsed = false;
        toggle.addEventListener('click', () => {
            collapsed = !collapsed;
            body?.classList.toggle('hidden');
            inputWrap?.classList.toggle('hidden');

            // Переключение ширины (flex-grow)
            chatContainer?.classList.toggle('flex-[6]');
            chatContainer?.classList.toggle('flex-[1]');

            toggle.style.transform = collapsed ? 'rotate(180deg)' : 'rotate(0deg)';
        });
    }


    const today = new Date();
    let viewDate = new Date(today.getFullYear(), today.getMonth(), 1);

    function renderCalendar() {
        const grid = document.getElementById('calendar-grid');
        const monthLabel = document.getElementById('month-label');
        if (!grid || !monthLabel) return;

        grid.innerHTML = '';
        const monthName = viewDate.toLocaleString('ru', { month: 'long', year: 'numeric' });
        monthLabel.innerText = monthName.replace(' г.', '').charAt(0).toUpperCase() + monthName.slice(1).replace(' г.', '');

        const year = viewDate.getFullYear();
        const month = viewDate.getMonth();

        let firstDay = new Date(year, month, 1).getDay();
        firstDay = firstDay === 0 ? 6 : firstDay - 1;

        const daysInMonth = new Date(year, month + 1, 0).getDate();

        for (let i = 0; i < firstDay; i++) {
            grid.innerHTML += '<span></span>';
        }

        for (let d = 1; d <= daysInMonth; d++) {
            const isToday = (d === today.getDate() && month === today.getMonth() && year === today.getFullYear());
            const span = document.createElement('span');
            span.innerText = d;
            span.className = isToday
                ? 'text-[#CC6200] font-[800] bg-[#CC6200]/10 rounded-sm'
                : 'p-1 hover:text-white cursor-pointer transition-colors';
            grid.appendChild(span);
        }
    }

    window.changeMonth = (n) => {
        viewDate.setMonth(viewDate.getMonth() + n);
        renderCalendar();
    };

    renderCalendar();
    const taskModal = document.getElementById('task-modal');
    const openTaskModalBtn = document.getElementById('open-task-modal');
    const closeTaskModalBtn = document.getElementById('close-task-modal');
    const taskForm = document.getElementById('task-form');
    const taskToast = document.getElementById('task-toast');

    function openTaskModal() {
    if (!taskModal) return;

    const dateInput = document.querySelector('input[name="date"]');
    const timeInput = document.querySelector('input[name="time"]');

    const now = new Date();

    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');

    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    if (dateInput && !dateInput.value) {
        dateInput.value = `${year}-${month}-${day}`;
    }

    if (timeInput && !timeInput.value) {
        timeInput.value = `${hours}:${minutes}`;
    }

    taskModal.classList.remove('hidden');
    taskModal.classList.add('flex');
    document.body.classList.add('overflow-hidden');
}

    function closeTaskModal() {
        if (!taskModal) return;
        taskModal.classList.add('hidden');
        taskModal.classList.remove('flex');
        document.body.classList.remove('overflow-hidden');
    }

    function showTaskToast() {
        if (!taskToast) return;

        taskToast.classList.remove('opacity-0', 'translate-y-[-20px]', 'pointer-events-none');
        taskToast.classList.add('opacity-100', 'translate-y-0');

        setTimeout(() => {
            taskToast.classList.add('opacity-0', 'translate-y-[-20px]', 'pointer-events-none');
            taskToast.classList.remove('opacity-100', 'translate-y-0');
        }, 2500);
    }

    openTaskModalBtn?.addEventListener('click', openTaskModal);
    closeTaskModalBtn?.addEventListener('click', closeTaskModal);

    taskModal?.addEventListener('click', (e) => {
        if (e.target === taskModal) {
            closeTaskModal();
        }
    });

    const taskDateInput = document.querySelector('input[name="date"]');
    const taskTimeInput = document.querySelector('input[name="time"]');

    if (taskDateInput && taskTimeInput) {

        function formatDate(date) {
            const y = date.getFullYear();
            const m = String(date.getMonth() + 1).padStart(2, '0');
            const d = String(date.getDate()).padStart(2, '0');
            return `${y}-${m}-${d}`;
        }

        function formatTime(date) {
            const h = String(date.getHours()).padStart(2, '0');
            const min = String(date.getMinutes()).padStart(2, '0');
            return `${h}:${min}`;
        }

        const today = new Date();

        taskDateInput.min = formatDate(today);

        const maxDate = new Date();
        maxDate.setDate(today.getDate() + 7);
        taskDateInput.max = formatDate(maxDate);

        function updateTimeLimit() {
            const selectedDate = taskDateInput.value;
            const todayStr = formatDate(new Date());

            if (selectedDate === todayStr) {
                taskTimeInput.min = formatTime(new Date());
            } else {
                taskTimeInput.min = "00:00";
            }
        }

        taskDateInput.addEventListener('change', updateTimeLimit);

        updateTimeLimit();
    }
    taskForm?.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(taskForm);
        const newTask = {
            title: formData.get('title'),
            date: formData.get('date'),
            time: formData.get('time'),
            priority: formData.get('priority'),
            department: formData.get('department'),
            comment: formData.get('comment')
        };

        console.log('Новая задача:', newTask);

        closeTaskModal();
        taskForm.reset();
        showTaskToast();
    });


    const shiftToggleBtn = document.getElementById('shift-toggle');
    const shiftToggleText = document.getElementById('shift-toggle-text');
    const shiftIndicator = document.getElementById('shift-indicator');

    const shiftModal = document.getElementById('shift-confirm-modal');
    const shiftModalTitle = document.getElementById('shift-modal-title');
    const shiftModalText = document.getElementById('shift-modal-text');
    const shiftCancelBtn = document.getElementById('shift-cancel-btn');
    const shiftConfirmBtn = document.getElementById('shift-confirm-btn');

    let shiftStarted = false;
    let confirmStep = 1;
    let shiftStartTime = null;
    let shiftTimerInterval = null;
    const shiftTimerWrap = document.getElementById('shift-timer-wrap');
    const shiftTimer = document.getElementById('shift-timer');

    function applyShiftUiOn(elapsedSeconds = 0) {
        shiftStarted = true;
        if (shiftToggleText) shiftToggleText.textContent = 'Закончить смену';
        shiftIndicator?.classList.remove('bg-[#22C55E]');
        shiftIndicator?.classList.add('bg-[#EF4444]');
        const label = shiftToggleBtn?.querySelector('p');
        if (label) label.textContent = 'Смена активна';
        startShiftTimer(elapsedSeconds);
    }

    function applyShiftUiOff() {
        shiftStarted = false;
        if (shiftToggleText) shiftToggleText.textContent = 'Начать смену';
        shiftIndicator?.classList.remove('bg-[#EF4444]');
        shiftIndicator?.classList.add('bg-[#22C55E]');
        const label = shiftToggleBtn?.querySelector('p');
        if (label) label.textContent = 'Статус';
        stopShiftTimer();
    }

    async function startShift() {
        try {
            await window.api.post('/api/shift/start/', {});
            applyShiftUiOn(0);
        } catch (err) {
            alert(err.message || 'Не удалось начать смену');
        }
    }

    async function endShift() {
        try {
            await window.api.post('/api/shift/end/', {});
            applyShiftUiOff();
        } catch (err) {
            alert(err.message || 'Не удалось завершить смену');
        }
    }

    // Восстановление статуса смены при загрузке страницы.
    (async () => {
        if (!window.api || !window.api.getToken()) return;
        try {
            const s = await window.api.get('/api/employee/status/');
            if (s.is_on_shift) {
                const eightH = 8 * 3600;
                const elapsed = s.remaining_shift_time != null ? eightH - s.remaining_shift_time : 0;
                applyShiftUiOn(Math.max(0, elapsed));
            }
        } catch { /* ничего */ }
    })();

    // Приветствие на employee_dashboard.html + карточка профиля на employee_tasks.html.
    (async () => {
        if (!window.api || !window.api.getToken()) return;
        const greetEl = document.getElementById('emp-greeting');
        const nameEl = document.getElementById('emp-name');                  // employee_dashboard
        const tasksNameEl = document.getElementById('emp-tasks-name');       // employee_tasks
        const tasksRoleEl = document.getElementById('emp-tasks-role');
        const tasksAvatarEl = document.getElementById('emp-tasks-avatar');

        if (greetEl) {
            const h = new Date().getHours();
            greetEl.textContent =
                h < 6  ? 'Доброй ночи' :
                h < 12 ? 'Доброе утро' :
                h < 18 ? 'Добрый день' :
                         'Добрый вечер';
        }

        let me = null;
        try {
            me = await window.api.get('/api/auth/me/');
        } catch (err) {
            const s = window.api.getSession();
            if (s.name || s.login) {
                me = { name: s.name, login: s.login, role: s.role };
            }
        }
        if (!me) return;

        const firstName = (me.name || '').trim().split(/\s+/)[0] || (me.login || '—');
        const initials = (me.name || '?').trim().split(/\s+/)
            .map(s => s[0] || '').slice(0, 2).join('').toUpperCase() || '?';

        if (nameEl) nameEl.textContent = firstName;
        if (tasksNameEl) tasksNameEl.textContent = me.name || me.login || '—';
        if (tasksRoleEl) tasksRoleEl.textContent =
            me.role === 'manager' ? 'Руководитель' : 'Сотрудник';
        if (tasksAvatarEl) tasksAvatarEl.textContent = initials;
    })();

    // Подгрузка задач для employee_dashboard.html — с автообновлением каждые 30 с
    let _dashFirstLoad = true;
    let _dashPrevIds   = new Set();

    async function _empDashLoad() {
        if (!window.api || !window.api.getToken()) return;
        const taskList = document.getElementById('emp-task-list');
        const attention = document.getElementById('emp-attention-list');
        const countEl   = document.getElementById('emp-active-count');
        const wordEl    = document.getElementById('emp-active-word');
        const barEl     = document.getElementById('emp-progress-bar');
        const labelEl   = document.getElementById('emp-progress-label');
        const totalEl   = document.getElementById('emp-progress-total');
        if (!taskList && !attention && !countEl && !barEl) return;

        try {
            const tickets = await window.api.get('/api/tickets/my/');
            const items   = tickets || [];

            // Оповещение о новых задачах при фоновом опросе
            if (!_dashFirstLoad) {
                const incoming = items.filter(t => !_dashPrevIds.has(t.id));
                if (incoming.length > 0) {
                    _empToast(incoming.length === 1
                        ? 'Новая задача назначена!'
                        : `Назначено новых задач: ${incoming.length}`);
                }
            }
            _dashPrevIds = new Set(items.map(t => t.id));

            // Счётчик активных + прогресс-бар «выполнено / всего».
            const active = items.filter(t => t.status === 'open' || t.status === 'assigned' || t.status === 'in_progress');
            const done   = items.filter(t => t.status === 'resolved' || t.status === 'closed');
            const total  = items.length;
            if (countEl) countEl.textContent = String(active.length);
            if (wordEl)  wordEl.textContent  = _pluralTasks(active.length);
            if (totalEl) totalEl.textContent = String(total);
            if (barEl) {
                const pct = total > 0 ? Math.round(done.length / total * 100) : 0;
                barEl.style.width = pct + '%';
            }
            if (labelEl) {
                labelEl.textContent = total > 0
                    ? `Выполнено ${done.length} из ${total}`
                    : 'Общая шкала выполненных задач';
            }

            if (taskList) {
                const newHtml = items.length === 0
                    ? '<p class="text-xs text-[#6B6B6B] text-center p-4">Нет задач</p>'
                    : items.map(t => `
                        <div class="task-item">
                            <span class="dot">•</span>
                            <div>
                                <p class="text-sm">${_e(t.category_name || 'Без категории')}</p>
                                <span class="muted">№${t.id} • ${_e(_emp_statusLabel(t.status))}</span>
                            </div>
                        </div>
                    `).join('');
                if (taskList.innerHTML.trim() !== newHtml.trim()) taskList.innerHTML = newHtml;
            }

            if (attention) {
                const now    = Date.now();
                const urgent = items.filter(t =>
                    t.status !== 'resolved' &&
                    t.status !== 'closed' &&
                    (t.deadline ? new Date(t.deadline).getTime() - now < 24 * 3600 * 1000 : t.priority >= 7)
                );
                const newHtml = urgent.length === 0
                    ? '<p class="text-xs text-[#6B6B6B] text-center py-6">Срочных задач нет</p>'
                    : urgent.map(t => `
                        <div class="bg-[#111111] border border-white/5 p-4 md:p-8 rounded-[5px] flex flex-col md:flex-row items-center justify-between gap-4 shrink-0">
                            <div class="flex flex-col md:flex-row items-center text-center md:text-left gap-4 md:gap-8">
                                <div class="bg-[#FF7A00] w-12 h-12 md:w-14 md:h-14 rounded-2xl flex items-center justify-center shrink-0"></div>
                                <div>
                                    <h4 class="font-[500] text-xl md:text-2xl uppercase tracking-tighter">Задача №${t.id}</h4>
                                    <p class="text-xs md:text-sm muted">${_e(t.category_name || 'Без категории')} • приоритет ${t.priority}</p>
                                </div>
                            </div>
                            <a class="w-full md:w-auto px-4 py-2 bg-[#1F1F1F] rounded-[5px] text-lg hover:bg-[#252525] border border-white/5 transition-colors hover:cursor-pointer"
                                href="employee_tasks.html">Открыть</a>
                        </div>
                    `).join('');
                if (attention.innerHTML.trim() !== newHtml.trim()) attention.innerHTML = newHtml;
            }
        } catch (err) {
            if (_dashFirstLoad) {
                const msg = `<p class="text-xs text-red-400 text-center p-4">Ошибка: ${_e(err.message || 'не удалось загрузить')}</p>`;
                if (taskList) taskList.innerHTML = msg;
                if (attention) attention.innerHTML = msg;
            }
        }
        _dashFirstLoad = false;
    }
    _empDashLoad();
    setInterval(_empDashLoad, 30000);
    // Мгновенные обновления через WebSocket
    window.addEventListener('ws:ticket_assigned',       _empDashLoad);
    window.addEventListener('ws:ticket_status_changed', _empDashLoad);

    function _e(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    function _emp_statusLabel(s) {
        return ({open:'Открыта', assigned:'Назначена', in_progress:'В работе',
                 resolved:'Выполнена', closed:'Закрыта', expired:'Просрочена'})[s] || s;
    }
    function _pluralTasks(n) {
        const abs = Math.abs(n) % 100;
        const last = abs % 10;
        if (abs >= 11 && abs <= 14) return 'задач';
        if (last === 1) return 'задача';
        if (last >= 2 && last <= 4) return 'задачи';
        return 'задач';
    }

    function openShiftModal(step = 1) {
        confirmStep = step;

        if (step === 1) {
            shiftModalTitle.textContent = 'Завершить смену?';
            shiftModalText.textContent = 'Вы уверены, что хотите завершить смену?';
            shiftConfirmBtn.textContent = 'Да';
        }

        if (step === 2) {
            shiftModalTitle.textContent = 'Последнее подтверждение';
            shiftModalText.textContent = 'После завершения смены задачи будут закрыты. Продолжить?';
            shiftConfirmBtn.textContent = 'Завершить';
        }

        shiftModal.classList.remove('hidden');
        shiftModal.classList.add('flex');
        document.body.classList.add('overflow-hidden');
    }

    function closeShiftModal() {
        shiftModal.classList.add('hidden');
        shiftModal.classList.remove('flex');
        document.body.classList.remove('overflow-hidden');
    }

    shiftToggleBtn?.addEventListener('click', () => {
        if (!shiftStarted) {
            startShift();
            return;
        }

        openShiftModal(1);
    });

    shiftCancelBtn?.addEventListener('click', closeShiftModal);

    shiftModal?.addEventListener('click', (e) => {
        if (e.target === shiftModal) closeShiftModal();
    });

    shiftConfirmBtn?.addEventListener('click', async () => {
        if (confirmStep === 1) {
            openShiftModal(2);
            return;
        }

        await endShift();
        closeShiftModal();
    });
    function formatShiftDuration(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
        const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
        const seconds = String(totalSeconds % 60).padStart(2, '0');

        return `${hours}:${minutes}:${seconds}`;
    }

    function startShiftTimer(elapsedSeconds = 0) {
        if (!shiftTimer || !shiftTimerWrap) return;

        shiftStartTime = new Date(Date.now() - elapsedSeconds * 1000);
        shiftTimerWrap.classList.remove('hidden');
        shiftTimer.textContent = formatShiftDuration(elapsedSeconds * 1000);

        if (shiftTimerInterval) {
            clearInterval(shiftTimerInterval);
        }

        shiftTimerInterval = setInterval(() => {
            const now = new Date();
            const diff = now - shiftStartTime;
            shiftTimer.textContent = formatShiftDuration(diff);
        }, 1000);
    }

    function stopShiftTimer() {
        if (shiftTimerInterval) {
            clearInterval(shiftTimerInterval);
            shiftTimerInterval = null;
        }

        shiftStartTime = null;

        if (shiftTimerWrap) {
            shiftTimerWrap.classList.add('hidden');
        }

        if (shiftTimer) {
            shiftTimer.textContent = '00:00:00';
        }
    }
});

// ===== ГЛОБАЛЬНЫЕ ФУНКЦ?? УПРАВЛЕН?Я =====

window.setChatQuery = function (text) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = text;
        input.focus();
    }
};

// Функция для Alpine.js (TaskManager)
// Этот объект Alpine подхватит автоматически при инициализации x-data="taskManager()"
// Мапинг статусов: бэк (Ticket.status) в†’ UI (taskManager).
const TICKET_STATUS_TO_UI = {
    open: 'assigned',
    assigned: 'assigned',
    in_progress: 'progress',
    resolved: 'done',
    closed: 'done',
    expired: 'done',
    declined: 'done',
};

function _ticketToTask(t) {
    // Если тикет ещё в очереди (status=open, исполнителя нет) — это значит, что
    // на момент создания все исполнители отдела были заняты. Очередь подхватит
    // его автоматически, как только кто-то освободится.
    const inQueue = t.status === 'open' && !t.assignee_name;

    return {
        id: t.id,
        title: t.category_name || 'Без категории',
        dept: t.assignee_name
            ? `Исполнитель: ${t.assignee_name}`
            : (inQueue ? '🕒 В очереди — ждём свободного исполнителя' : 'Не назначен'),
        // Кто заявил о проблеме (creator) и кто реально распределил исполнителя
        // (assigner из TicketAssignment). Если ещё никто не назначен — диспетчер
        // ещё не определён (тикет в очереди ИИ-агента).
        initiator: t.creator_name || '—',
        assigner: inQueue
            ? '🤖 ИИ-агент «Вектор» (ожидание)'
            : (t.assigner_name || '🤖 ИИ-агент «Вектор»'),
        comment: t.description,
        status: inQueue ? 'queued' : (TICKET_STATUS_TO_UI[t.status] || 'assigned'),
        rawStatus: t.status,
        deadline: t.deadline ? new Date(t.deadline).toLocaleTimeString('ru', {hour: '2-digit', minute: '2-digit'}) : 'Без срока',
        assigneeId: t.assignee_id,
        priority: t.priority,
        isOverdue: Boolean(t.deadline && new Date(t.deadline).getTime() < Date.now() && !['resolved', 'closed'].includes(t.status)),
    };
}

function taskManager() {
    return {
        search: '',
        filter: 'all',
        showConfirm: false,
        showDecline: false,
        pendingTaskId: null,
        declineTaskId: null,
        declineReason: '',
        declineNotMine: false,
        loading: false,
        loadError: null,
        tasks: [],
        meetings: [],
        currentEmployeeId: null,
        _pollInterval: null,

        async init() {
            if (!window.api || !window.api.requireAuth()) return;
            const session = window.api.getSession();
            this.currentEmployeeId = session.employeeId ? Number(session.employeeId) : null;
            await this.reload();
            // Фоновый опрос каждые 30 секунд — резервный механизм
            this._pollInterval = setInterval(() => this._backgroundPoll(), 30000);
            // Мгновенные обновления через WebSocket (если ws.js подключён)
            window.addEventListener('ws:ticket_assigned',       () => this._backgroundPoll());
            window.addEventListener('ws:ticket_status_changed', () => this._backgroundPoll());
        },

        async reload() {
            this.loading = true;
            this.loadError = null;
            try {
                const myList = await window.api.get('/api/tickets/my/');
                const items = myList || [];
                this._updateProfileProgress(items);
                this.tasks = items.map(_ticketToTask);
            } catch (err) {
                this.loadError = err.message || 'Не удалось загрузить задачи';
                this.tasks = [];
            } finally {
                this.loading = false;
            }
        },

        // Тихий фоновый опрос — не меняет loading, показывает тост при новых задачах
        async _backgroundPoll() {
            if (!window.api || !window.api.getToken()) return;
            try {
                const myList = await window.api.get('/api/tickets/my/');
                const items  = myList || [];
                const oldIds = new Set(this.tasks.map(t => t.id));
                const incoming = items.filter(t => !oldIds.has(t.id));
                this._updateProfileProgress(items);
                this.tasks = items.map(_ticketToTask);
                if (incoming.length > 0) {
                    _empToast(incoming.length === 1
                        ? 'Новая задача назначена!'
                        : `Назначено новых задач: ${incoming.length}`);
                }
            } catch (_) { /* фоновый опрос — ошибку не показываем */ }
        },

        _updateProfileProgress(myTickets) {
            // Шкала прогресса в карточке профиля на employee_tasks.html.
            const wrap = document.getElementById('emp-tasks-progress-wrap');
            const bar = document.getElementById('emp-tasks-progress-bar');
            const pctEl = document.getElementById('emp-tasks-progress-pct');
            const totalEl = document.getElementById('emp-tasks-progress-total');
            if (!bar && !pctEl && !totalEl) return;

            const total = myTickets.length;
            const done = myTickets.filter(t =>
                t.status === 'resolved' || t.status === 'closed').length;
            const pct = total > 0 ? Math.round(done / total * 100) : 0;
            if (bar) bar.style.width = pct + '%';
            if (pctEl) pctEl.textContent = pct + '%';
            if (totalEl) totalEl.textContent = String(total);
            if (wrap) wrap.title = `${done} из ${total} задач`;
        },

        // Функция расчета оставшегося времени
        getTimeUntil(targetTime) {
            const now = new Date();
            const [hours, minutes] = targetTime.split(':');

            const target = new Date();
            target.setHours(parseInt(hours), parseInt(minutes), 0);

            // Если время уже прошло (напр. встреча была в 10:00, а сейчас 12:00)
            if (target < now) return 'уже началось';

            const diffMs = target - now; // разница в миллисекундах
            const diffMins = Math.floor(diffMs / 60000);
            const h = Math.floor(diffMins / 60);
            const m = diffMins % 60;

            if (h > 0) {
                return `через ${h}ч ${m}мин`;
            } else {
                return `через ${m}мин`;
            }
        },
        get filteredTasks() {
            return this.tasks.filter(task => {
                const matchesSearch = task.title.toLowerCase().includes(this.search.toLowerCase()) ||
                    task.id.toString().includes(this.search);
                const matchesFilter = this.filter === 'all' || task.status === this.filter;
                return matchesSearch && matchesFilter;
            });
        },

        statusStyles: {
            queued: { label: 'В очереди' },
            assigned: { label: 'Принять' },
            progress: { label: 'В работе' },
            done: { label: 'Выполнено' }
        },

        async changeStatus(id) {
            const task = this.tasks.find(t => t.id === id);
            if (!task) return;
            if (task.status === 'queued') return;

            if (task.status === 'assigned') {
                try {
                    const resp = await window.api.patch(`/api/tickets/${id}/accept/`, {});
                    task.rawStatus = resp.status;
                    task.status = TICKET_STATUS_TO_UI[resp.status] || 'progress';
                } catch (err) {
                    alert(err.message || 'Не удалось принять задачу');
                }
            } else if (task.status === 'progress') {
                this.pendingTaskId = id;
                this.showConfirm = true;
            }
        },

        async declineTask(id) {
            this.declineTaskId = id;
            this.declineReason = '';
            this.declineNotMine = false;
            this.showDecline = true;
            return;
            if (!confirm('Отклонить задачу?')) return;
            try {
                const resp = await window.api.patch(`/api/tickets/${id}/decline/`, {});
                this.tasks = this.tasks.filter(t => t.id !== id);
            } catch (err) {
                alert(err.message || 'Не удалось отклонить задачу');
            }
        },

        async confirmDone() {
            const id = this.pendingTaskId;
            if (!id) { this.showConfirm = false; return; }
            try {
                const resp = await window.api.patch(`/api/tickets/${id}/complete/`, {});
                const task = this.tasks.find(t => t.id === id);
                if (task) {
                    task.rawStatus = resp.status;
                    task.status = TICKET_STATUS_TO_UI[resp.status] || 'done';
                }
            } catch (err) {
                alert(err.message || 'Не удалось завершить задачу');
            } finally {
                this.showConfirm = false;
                this.pendingTaskId = null;
            }
        },

        cancelDone() {
            this.showConfirm = false;
            this.pendingTaskId = null;
        }
    }
}



function supportChat() {
    return {
        userInput: '',
        showInitialButtons: true,
        messages: [],
        selectedFile: null, // Добавили сюда переменную файла

        // Вызов окна выбора файла
        triggerFileSelect() {
            document.getElementById('file-input').click();
        },

        // Обработка файла
        handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                this.selectedFile = file;
            }
        },

        connectOperator() {
            this.showInitialButtons = false;
            this.addMessage('user', 'Нет, соедини меня с оператором');
            setTimeout(() => {
                this.addMessage('bot', 'Хорошо, уже позвал сотрудника технической поддержки. Пожалуйста, ожидайте ответа в этом чате.');
            }, 800);
        },

        tryAI() {
            this.showInitialButtons = false;
            this.addMessage('user', 'Да, давай попробуем');
            setTimeout(() => {
                this.addMessage('bot', 'Делаю запрос к интеллектуальной системе "ВЕКТОР-??"...');
                setTimeout(() => {
                    this.addMessage('bot', 'Ошибка: API-ключ не найден. Система ?? временно недоступна. Пожалуйста, введите ваш вопрос вручную для оператора.');
                }, 1500);
            }, 800);
        },

        sendMessage() {
            // Если есть и текст, и файл — отправляем вместе
            if (this.userInput.trim() === '' && !this.selectedFile) return;

            let messageText = this.userInput;
            if (this.selectedFile) {
                messageText += ` (Файл: ${this.selectedFile.name})`;
            }

            this.addMessage('user', messageText);

            // Сброс полей
            this.userInput = '';
            this.selectedFile = null;
            this.showInitialButtons = false;

            setTimeout(() => {
                this.addMessage('bot', 'Ваше сообщение получено. Оператор свяжется с вами.');
            }, 1000);
        },

        addMessage(role, text) {
            this.messages.push({ id: Date.now(), role, text });
            this.$nextTick(() => {
                const win = document.getElementById('chat-window');
                if (win) win.scrollTo({ top: win.scrollHeight, behavior: 'smooth' });
            });
        }
    }
}

window.confirmEmployeeDecline = async function(component) {
    const id = component.declineTaskId;
    if (!id) return;
    try {
        await window.api.patch(`/api/tickets/${id}/decline/`, {
            reason: component.declineReason || '',
            not_mine: Boolean(component.declineNotMine),
        });
        component.tasks = component.tasks.filter(t => t.id !== id);
    } catch (err) {
        alert(err.message || 'Не удалось отклонить задачу');
    } finally {
        component.showDecline = false;
        component.declineTaskId = null;
        component.declineReason = '';
        component.declineNotMine = false;
    }
};

// ─── Toast-уведомление о новых задачах ──────────────────────────────────────
function _empToast(msg) {
    var el = document.getElementById('_emp-toast-notif');
    if (!el) {
        el = document.createElement('div');
        el.id = '_emp-toast-notif';
        el.style.cssText = [
            'position:fixed;top:24px;left:50%;z-index:9999',
            'transform:translateX(-50%) translateY(-16px)',
            'opacity:0;pointer-events:none',
            'background:#151515;border:1px solid rgba(255,122,0,.5)',
            'color:#fff;padding:10px 22px;border-radius:8px',
            'font-size:14px;font-family:inherit',
            'box-shadow:0 4px 24px rgba(0,0,0,.5)',
            'transition:opacity .25s,transform .25s;white-space:nowrap'
        ].join(';');
        document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.opacity = '1';
    el.style.transform = 'translateX(-50%) translateY(0)';
    clearTimeout(el._t);
    el._t = setTimeout(function() {
        el.style.opacity = '0';
        el.style.transform = 'translateX(-50%) translateY(-16px)';
    }, 3500);
}

// ═══════════════════════════════════════════════════════════
// SIDEBAR CHAT — полноценный ИИ-чат в боковой панели
// ═══════════════════════════════════════════════════════════

function _scEsc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

let _scCatsCache = null;
async function _scLoadCats() {
    if (_scCatsCache) return _scCatsCache;
    try { _scCatsCache = await window.api.get('/api/categories/'); }
    catch (_) { _scCatsCache = []; }
    return _scCatsCache;
}

function _scBotMsg(html) {
    const box = document.getElementById('sidebar-chat-box');
    if (!box) return;
    const el = document.createElement('div');
    el.className = 'flex gap-2 items-start';
    el.innerHTML = `
        <img src="images/ВЕКТОР.svg" style="width:20px;height:20px;opacity:.6;flex-shrink:0;margin-top:2px">
        <div style="background:#1A1A1A;border:1px solid rgba(255,255,255,.06);padding:8px 12px;border-radius:12px;border-top-left-radius:2px;font-size:12px;line-height:1.5;color:#fff">${html}</div>`;
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
}

function _scUserMsg(text) {
    const box = document.getElementById('sidebar-chat-box');
    if (!box) return;
    const el = document.createElement('div');
    el.style.cssText = 'display:flex;justify-content:flex-end';
    const inner = document.createElement('div');
    inner.style.cssText = 'background:rgba(255,122,0,.12);border:1px solid rgba(255,122,0,.3);padding:8px 12px;border-radius:12px;border-top-right-radius:2px;font-size:12px;line-height:1.5;color:#fff;max-width:90%';
    inner.textContent = text;
    el.appendChild(inner);
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
}

let _scPendingForm = null;
let _scPendingText = '';

window.sidebarSendMessage = function(preset) {
    const input = document.getElementById('sidebar-chat-input');
    const text  = preset || (input ? input.value.trim() : '');
    if (!text) return;
    if (input && !preset) input.value = '';

    // Показываем сообщение пользователя (не для внутренних кодов)
    if (!preset || !preset.startsWith('__')) _scUserMsg(text);

    if (!window.api || !window.api.getToken()) {
        _scBotMsg('Необходимо войти в систему.');
        return;
    }

    // Обработка быстрых кнопок по коду
    if (preset === '__show_tasks__') {
        _scUserMsg('Покажи мои активные задачи');
        _scBotMsg('Ваши задачи отображаются в центральном списке. Используйте фильтр «В работе» или «Назначено» чтобы увидеть только активные.');
        return;
    }
    if (preset === '__connect_manager__') {
        _scUserMsg('Соедини меня с управляющим');
        _scBotMsg('Уведомление менеджеру отправлено. Он свяжется с вами в ближайшее время.');
        return;
    }

    // Любой текст из поля → создание заявки
    _scShowForm(text);
};

function _scShowForm(text) {
    if (_scPendingForm) { _scPendingForm.remove(); _scPendingForm = null; }
    _scPendingText = text;
    const box = document.getElementById('sidebar-chat-box');
    if (!box) return;

    const wrap = document.createElement('div');
    wrap.id = 'sc-pending-form';
    wrap.style.cssText = 'display:flex;gap:8px;align-items:flex-start';
    wrap.innerHTML = `
        <img src="images/ВЕКТОР.svg" style="width:20px;height:20px;opacity:.6;flex-shrink:0;margin-top:2px">
        <div style="background:#1A1A1A;border:1px solid rgba(255,255,255,.06);padding:10px 12px;border-radius:12px;border-top-left-radius:2px;font-size:12px;color:#fff;flex:1;min-width:0">
            <p style="color:#B3B3B3;margin-bottom:6px">Создать заявку по описанию?</p>
            <p style="font-size:10px;color:#6B6B6B;margin-bottom:8px;word-break:break-word">${_scEsc(text.slice(0, 100))}${text.length > 100 ? '…' : ''}</p>
            <select id="sc-priority" style="width:100%;background:#0D0D0D;border:1px solid rgba(255,255,255,.1);color:#fff;border-radius:8px;padding:5px 8px;font-size:11px;margin-bottom:8px;outline:none">
                <option value="3">Низкая критичность</option>
                <option value="5" selected>Обычная</option>
                <option value="7">Высокая</option>
                <option value="10">Критическая</option>
            </select>
            <div id="sc-form-err" style="display:none;color:#f87171;font-size:10px;margin-bottom:6px"></div>
            <div style="display:flex;gap:8px">
                <button id="sc-submit-btn"
                    style="flex:1;background:#FF7A00;color:#fff;border:none;border-radius:8px;padding:6px;font-size:11px;font-weight:600;cursor:pointer">
                    Отправить
                </button>
                <button id="sc-cancel-btn"
                    style="flex:1;background:#1F1F1F;color:#fff;border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:6px;font-size:11px;cursor:pointer">
                    Отмена
                </button>
            </div>
        </div>`;

    box.appendChild(wrap);
    _scPendingForm = wrap;
    box.scrollTop = box.scrollHeight;

    // Привязываем обработчики через JS — надёжнее inline-onclick внутри Alpine
    wrap.querySelector('#sc-submit-btn').addEventListener('click', window.sidebarCreateTicket);
    wrap.querySelector('#sc-cancel-btn').addEventListener('click', window.sidebarCancelTicket);
}

window.sidebarCancelTicket = function() {
    if (_scPendingForm) { _scPendingForm.remove(); _scPendingForm = null; }
    _scPendingText = '';
    _scBotMsg('Хорошо, заявку не создаю. Напишите новое обращение когда будет нужно.');
};

window.sidebarCreateTicket = async function() {
    const priorityEl = document.getElementById('sc-priority');
    const errEl      = document.getElementById('sc-form-err');
    const submitBtn  = document.getElementById('sc-submit-btn');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = '…'; }
    if (errEl) errEl.style.display = 'none';

    try {
        const [data, cats] = await Promise.all([
            window.api.post('/api/agent/classify/', {
                text:     _scPendingText,
                priority: parseInt(priorityEl ? priorityEl.value : '5', 10),
            }),
            _scLoadCats(),
        ]);

        if (_scPendingForm) { _scPendingForm.remove(); _scPendingForm = null; }
        _scPendingText = '';

        const pct     = Math.round((data.confidence || 0) * 100);
        const rcId    = 'sc-rc-' + data.ticket_id;
        const catOpts = cats.map(function(c) { return '<option value="' + c.id + '">' + _scEsc(c.name) + '</option>'; }).join('');
        const assignee = data.assignee_name
            ? 'Исполнитель: <span style="color:#FF7A00">' + _scEsc(data.assignee_name) + '</span>'
            : '🕒 В очереди — свободный сотрудник подхватит задачу';

        const rcBlock = cats.length > 0
            ? '<div id="' + rcId + '-block" style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.06)">' +
              '<p style="font-size:10px;color:#6B6B6B;margin-bottom:4px">Категория неверная? Исправьте:</p>' +
              '<div style="display:flex;gap:4px">' +
              '<select id="' + rcId + '-select" style="flex:1;background:#0D0D0D;border:1px solid rgba(255,255,255,.1);color:#fff;border-radius:6px;padding:3px 6px;font-size:10px;outline:none">' +
              '<option value="">— выберите —</option>' + catOpts + '</select>' +
              '<button data-ticket-id="' + data.ticket_id + '" data-rc-id="' + rcId + '" class="sc-reclass-btn" ' +
              'style="background:#FF7A00;color:#fff;border:none;border-radius:6px;padding:3px 8px;font-size:10px;cursor:pointer">✓</button>' +
              '</div></div>'
            : '';

        _scBotMsg('<span style="color:#22C55E;font-weight:600">Заявка №' + data.ticket_id + ' создана!</span><br>' +
            'Категория: <span style="color:#FF7A00" id="' + rcId + '-cat">' + _scEsc(data.category) + '</span> (' + pct + '%)<br>' +
            assignee + rcBlock);
    } catch (err) {
        if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Отправить'; }
        if (errEl) { errEl.textContent = err.message || 'Не удалось создать заявку'; errEl.style.display = 'block'; }
    }
};

// Делегирование клика для кнопок переназначения категории
document.addEventListener('click', async function(e) {
    const btn = e.target.closest('.sc-reclass-btn');
    if (!btn) return;
    const ticketId = btn.dataset.ticketId;
    const rcId     = btn.dataset.rcId;
    const select   = document.getElementById(rcId + '-select');
    if (!select || !select.value) { if (select) select.style.borderColor = '#f87171'; return; }
    btn.disabled = true; btn.textContent = '…';
    try {
        const data = await window.api.patch('/api/tickets/' + ticketId + '/reclassify/', { category_id: parseInt(select.value) });
        const catEl  = document.getElementById(rcId + '-cat');
        const block  = document.getElementById(rcId + '-block');
        if (catEl) catEl.textContent = data.category;
        if (block) block.innerHTML = '<p style="font-size:10px;color:#22C55E">Категория изменена: <strong>' + _scEsc(data.category) + '</strong></p>';
    } catch (err) {
        btn.disabled = false; btn.textContent = '✓';
    }
});

// Переключение (свернуть / развернуть) боковую панель — вызывается из onclick в HTML
window.scToggle = function() {
    var b = document.getElementById('sc-body');
    var c = document.getElementById('sc-chevron');
    if (!b) return;
    var hidden = b.style.display === 'none';
    b.style.display = hidden ? 'flex' : 'none';
    if (c) c.style.transform = hidden ? '' : 'rotate(180deg)';
};

// Приветственное сообщение — скрипт находится в конце <body>, DOM уже построен,
// поэтому вызываем немедленно, без ожидания DOMContentLoaded / load.
(function() {
    var box = document.getElementById('sidebar-chat-box');
    if (box && box.children.length === 0) {
        _scBotMsg('Здравствуйте! Опишите проблему — я создам заявку, ИИ определит категорию и назначит исполнителя.');
    }
})();
