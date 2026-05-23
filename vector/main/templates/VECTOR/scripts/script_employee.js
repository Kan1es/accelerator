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

    // Подгрузка задач для employee_dashboard.html
    (async () => {
        if (!window.api || !window.api.getToken()) return;
        const taskList = document.getElementById('emp-task-list');
        const attention = document.getElementById('emp-attention-list');
        const countEl = document.getElementById('emp-active-count');
        const wordEl = document.getElementById('emp-active-word');
        const barEl = document.getElementById('emp-progress-bar');
        const labelEl = document.getElementById('emp-progress-label');
        const totalEl = document.getElementById('emp-progress-total');
        if (!taskList && !attention && !countEl && !barEl) return;

        try {
            const tickets = await window.api.get('/api/tickets/my/');
            const items = tickets || [];

            // Счётчик активных + прогресс-бар «выполнено / всего».
            const active = items.filter(t => t.status === 'open' || t.status === 'assigned' || t.status === 'in_progress');
            const done = items.filter(t => t.status === 'resolved' || t.status === 'closed');
            const total = items.length;
            if (countEl) countEl.textContent = String(active.length);
            if (wordEl) wordEl.textContent = _pluralTasks(active.length);
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
                if (items.length === 0) {
                    taskList.innerHTML = '<p class="text-xs text-[#6B6B6B] text-center p-4">Нет задач</p>';
                } else {
                    taskList.innerHTML = items.map(t => `
                        <div class="task-item">
                            <span class="dot">•</span>
                            <div>
                                <p class="text-sm">${_e(t.category_name || 'Без категории')}</p>
                                <span class="muted">№${t.id} • ${_e(_emp_statusLabel(t.status))}</span>
                            </div>
                        </div>
                    `).join('');
                }
            }

            if (attention) {
                const now = Date.now();
                const urgent = items.filter(t =>
                    t.status !== 'resolved' &&
                    t.status !== 'closed' &&
                    (t.deadline ? new Date(t.deadline).getTime() - now < 24 * 3600 * 1000 : t.priority >= 7)
                );
                if (urgent.length === 0) {
                    attention.innerHTML = '<p class="text-xs text-[#6B6B6B] text-center py-6">Срочных задач нет</p>';
                } else {
                    attention.innerHTML = urgent.map(t => `
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
                }
            }
        } catch (err) {
            const msg = `<p class="text-xs text-red-400 text-center p-4">Ошибка: ${_e(err.message || 'не удалось загрузить')}</p>`;
            if (taskList) taskList.innerHTML = msg;
            if (attention) attention.innerHTML = msg;
        }
    })();

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

// ===== ГЛОБАЛЬНЫЕ ФУНКЦИИ УПРАВЛЕНИЯ =====

window.setChatQuery = function (text) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = text;
        input.focus();
    }
};

// Функция для Alpine.js (TaskManager)
// Этот объект Alpine подхватит автоматически при инициализации x-data="taskManager()"
// Мапинг статусов: бэк (Ticket.status) → UI (taskManager).
const TICKET_STATUS_TO_UI = {
    open: 'assigned',
    assigned: 'assigned',
    in_progress: 'progress',
    resolved: 'done',
    closed: 'done',
    expired: 'done',
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
        status: TICKET_STATUS_TO_UI[t.status] || 'assigned',
        rawStatus: t.status,
        deadline: t.deadline ? new Date(t.deadline).toLocaleTimeString('ru', {hour: '2-digit', minute: '2-digit'}) : 'Без срока',
        assigneeId: t.assignee_id,
        priority: t.priority,
    };
}

function taskManager() {
    return {
        search: '',
        filter: 'all',
        showConfirm: false,
        pendingTaskId: null,
        loading: false,
        loadError: null,
        tasks: [],
        meetings: [],
        currentEmployeeId: null,

        async init() {
            if (!window.api || !window.api.requireAuth()) return;
            const session = window.api.getSession();
            this.currentEmployeeId = session.employeeId ? Number(session.employeeId) : null;
            await this.reload();
        },

        async reload() {
            this.loading = true;
            this.loadError = null;
            try {
                // «Мои задачи» = тикеты, где текущий пользователь — assignee.
                // /api/tickets/my/ отдаёт именно их (включая resolved/closed для
                // расчёта прогресс-бара слева).
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
            assigned: { label: 'Принять' },
            progress: { label: 'В работе' },
            done: { label: 'Выполнено' }
        },

        async changeStatus(id) {
            const task = this.tasks.find(t => t.id === id);
            if (!task) return;

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
                this.addMessage('bot', 'Делаю запрос к интеллектуальной системе "ВЕКТОР-ИИ"...');
                setTimeout(() => {
                    this.addMessage('bot', 'Ошибка: API-ключ не найден. Система ИИ временно недоступна. Пожалуйста, введите ваш вопрос вручную для оператора.');
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