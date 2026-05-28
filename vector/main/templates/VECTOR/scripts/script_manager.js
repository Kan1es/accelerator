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


function _ticketCard(t) {
    const isDeclined = t.status === 'declined';
    const isOverdue = t.deadline && new Date(t.deadline).getTime() < Date.now() && !['resolved', 'closed'].includes(t.status);
    const assignee = t.assignee_name || (t.status === 'open' ? 'в очереди, свободных нет' : 'не назначен');
    const declineBlock = isDeclined ? `
        <div class="bg-red-500/10 border border-red-500/30 rounded-[5px] p-3 text-xs text-red-100">
          <p>Отказался: ${_esc(t.declined_by_name || '—')}</p>
          <p>Причина: ${_esc(t.decline_reason || 'не указана')}</p>
          <p>${t.decline_not_mine ? 'Отмечено: задача не моя' : 'Без отметки "задача не моя"'}</p>
        </div>` : '';
    const reassignButton = isDeclined ? `<button class="js-reassign-ticket mt-2 text-xs px-3 py-2 rounded border border-[#FF7A00] text-[#FF7A00] hover:bg-[#FF7A00]/10" data-ticket-id="${t.id}">Назначить заново</button>` : '';
    return `
      <div class="bg-[#151515] border ${isDeclined || isOverdue ? 'border-red-500/50' : 'border-white/5'} rounded-[5px] p-4 flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <p class="font-semibold">Задача №${t.id}</p>
          <span class="text-xs ${isDeclined || isOverdue ? 'text-red-400' : 'text-[#FF9A3C]'}">${_esc(TICKET_STATUS_LABELS[t.status] || t.status)}</span>
        </div>
        <p class="text-sm text-[#B3B3B3]">${_esc(t.description)}</p>
        ${declineBlock}
        <div class="text-xs text-[#6B6B6B] flex flex-wrap gap-3">
          <span>Категория: ${_esc(t.category_name || '—')}</span>
          <span>Исполнитель: ${_esc(assignee)}</span>
          <span>Приоритет: ${t.priority}</span>
          ${isOverdue ? '<span class="text-red-400">Дедлайн просрочен</span>' : ''}
        </div>
        ${reassignButton}
      </div>`;
}

document.addEventListener('click', async (event) => {
    const btn = event.target.closest('.js-reassign-ticket');
    if (!btn) return;
    const ticketId = btn.dataset.ticketId;
    const employees = await window.api.get('/api/employees/');
    const choices = employees.filter(e => e.is_on_shift && !e.is_busy);
    if (!choices.length) {
        alert('Нет свободных сотрудников на смене');
        return;
    }
    const message = choices.map(e => `${e.id}: ${e.name}`).join('\n');
    const raw = prompt(`Введите ID исполнителя:\n${message}`);
    if (!raw) return;
    try {
        await window.api.patch(`/api/tickets/${ticketId}/reassign/`, { assignee_id: parseInt(raw, 10) });
        await loadTasksGrid();
        if (typeof loadMgrActiveTasks === 'function') await loadMgrActiveTasks();
    } catch (err) {
        alert(err.message || 'Не удалось переназначить задачу');
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
async function _populateTaskFormSelects() {
    if (!window.api || !window.api.getToken()) return;
    const empSel = document.getElementById('task-form-assignee');
    const catSel = document.getElementById('task-form-category');
    try {
        if (empSel) {
            const employees = await window.api.get('/api/employees/');
            empSel.innerHTML = '<option value="">— выберите сотрудника —</option>' +
                (employees || []).map(e =>
                    `<option value="${e.id}">${e.name}${e.is_busy ? ' (занят)' : ''}</option>`
                ).join('');
        }
        if (catSel) {
            const cats = await window.api.get('/api/categories/');
            catSel.innerHTML = '<option value="">— выберите категорию —</option>' +
                (cats || []).map(c =>
                    `<option value="${c.id}">${c.name}</option>`
                ).join('');
        }
    } catch (err) {
        console.warn('Не удалось загрузить справочники:', err);
    }
}

// Заполняем select-ы при открытии модалки.
const _origOpenTaskModal = typeof openTaskModal === 'function' ? openTaskModal : null;
window.openTaskModal = function () {
    if (_origOpenTaskModal) _origOpenTaskModal();
    _populateTaskFormSelects();
};
// Если кнопка уже была привязана к старой openTaskModal, перепривяжем.
document.getElementById('open-task-modal')?.addEventListener('click', _populateTaskFormSelects);

taskForm?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(taskForm);
    const title = (formData.get('title') || '').trim();
    const comment = (formData.get('comment') || '').trim();
    const date = formData.get('date');
    const time = formData.get('time');
    const priority = parseInt(formData.get('priority') || '5', 10);
    const categoryId = formData.get('category_id');
    const assigneeId = formData.get('assignee_id');

    const errBox = document.getElementById('task-form-error');
    const showErr = (msg) => {
        if (!errBox) { alert(msg); return; }
        errBox.textContent = msg;
        errBox.classList.remove('hidden');
    };
    errBox?.classList.add('hidden');

    if (!title) { showErr('Укажите название задачи'); return; }
    if (!assigneeId) { showErr('Выберите исполнителя'); return; }

    let deadlineIso = null;
    if (date && time) {
        deadlineIso = new Date(`${date}T${time}:00`).toISOString();
    }

    const description = comment ? `${title}\n\n${comment}` : title;

    try {
        await window.api.post('/api/tickets/', {
            description,
            category_id: categoryId ? Number(categoryId) : null,
            assignee_id: Number(assigneeId),
            priority,
            deadline: deadlineIso,
        });
        closeTaskModal();
        taskForm.reset();
        showTaskToast();
        // Если на странице есть таблицы тикетов/сотрудников — обновим.
        if (typeof loadTasksGrid === 'function' && document.getElementById('tasks-grid')) loadTasksGrid();
        if (typeof loadWorkersGrid === 'function' && document.getElementById('workers-grid')) loadWorkersGrid();
    } catch (err) {
        showErr(err.message || 'Не удалось создать задачу');
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const timers = document.querySelectorAll(".task-timer");

    function toSeconds(time) {
        const [h, m, s] = time.split(":").map(Number);
        return h * 3600 + m * 60 + s;
    }

    function toTime(seconds) {
        const h = String(Math.floor(seconds / 3600)).padStart(2, "0");
        const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
        const s = String(seconds % 60).padStart(2, "0");
        return `${h}:${m}:${s}`;
    }

    const timerData = Array.from(timers).map((timer, index) => {
        const key = `task-timer-${index}`;

        let savedEndTime = localStorage.getItem(key);

        if (!savedEndTime) {
            const startSeconds = toSeconds(timer.dataset.time);
            savedEndTime = Date.now() + startSeconds * 1000;
            localStorage.setItem(key, savedEndTime);
        }

        return {
            el: timer,
            key,
            endTime: Number(savedEndTime)
        };
    });

    function updateTimers() {
        timerData.forEach(timer => {
            const left = Math.floor((timer.endTime - Date.now()) / 1000);

            if (left <= 0) {
                timer.el.textContent = "00:00:00";
                localStorage.removeItem(timer.key);
            } else {
                timer.el.textContent = toTime(left);
            }
        });
    }

    updateTimers();
    setInterval(updateTimers, 1000);
});

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
document.addEventListener('DOMContentLoaded', () => {

    // в”Ђв”Ђв”Ђ PROFILE PANEL (manager_workers.html) в”Ђв”Ђ───────────────────────
    // Открывается при клике по карточке сотрудника. Тянет реальные данные.

    function _initials(name) {
        return (name || '?').trim().split(/\s+/).map(s => s[0] || '').slice(0, 2).join('').toUpperCase() || '?';
    }

    async function openProfile(id, name, role) {
        if (!window.api || !window.api.getToken()) return;
        const panel = document.getElementById('profile-panel');
        if (!panel) return;

        const avatarEl = document.getElementById('p-avatar');
        const nameEl   = document.getElementById('p-name');
        const roleEl   = document.getElementById('p-role');
        if (avatarEl) avatarEl.textContent = _initials(name);
        if (nameEl)   nameEl.textContent   = name || '—';
        if (roleEl)   roleEl.textContent   = role || '—';
        const progressEl = document.getElementById('p-progress');
        const percentEl  = document.getElementById('p-percent');
        if (progressEl) progressEl.style.width = '0%';
        if (percentEl)  percentEl.textContent  = '0%';

        panel.classList.add('open');
        document.body.style.overflow = 'hidden';

        try {
            const tickets = await window.api.get('/api/tickets/my/?assignee=' + encodeURIComponent(id));
            const items = tickets || [];
            const done = items.filter(t => t.status === 'resolved' || t.status === 'closed').length;
            const active = items.filter(t => t.status === 'assigned' || t.status === 'in_progress');
            const upcoming = items.filter(t => t.status === 'open');
            const doneItems = items.filter(t => t.status === 'resolved' || t.status === 'closed');

            const pct = items.length > 0 ? Math.round(done / items.length * 100) : 0;
            if (progressEl) progressEl.style.width = pct + '%';
            if (percentEl)  percentEl.textContent  = pct + '%';

            const activeWrap = document.getElementById('p-active-tasks');
            if (activeWrap) {
                activeWrap.innerHTML = active.length === 0
                    ? '<p class="text-xs text-[#6B6B6B]">Активных задач нет</p>'
                    : active.map(t => `
                        <div class="task-card-sm flex justify-between items-center gap-4">
                            <div>
                                <h3 class="font-semibold text-sm">Задача №${t.id}</h3>
                                <p class="text-[11px] text-[#6B6B6B]">${_esc(t.category_name || '—')}</p>
                            </div>
                            <span class="badge-working shrink-0"><span class="w-1.5 h-1.5 rounded-full bg-[#F59E0B] inline-block"></span>${t.status === 'in_progress' ? 'В работе' : 'Назначена'}</span>
                        </div>
                    `).join('');
            }
            const upWrap = document.getElementById('p-upcoming-tasks');
            if (upWrap) {
                upWrap.innerHTML = upcoming.length === 0
                    ? '<p class="text-xs text-[#6B6B6B]">Нет</p>'
                    : upcoming.map(t => `
                        <div class="task-card-sm">
                            <div class="flex justify-between items-start gap-4">
                                <div>
                                    <h3 class="font-semibold text-sm">Задача №${t.id}</h3>
                                    <p class="text-[11px] text-[#6B6B6B]">${_esc(t.category_name || '—')}</p>
                                </div>
                                <div class="text-right shrink-0">
                                    <p class="text-[10px] text-[#6B6B6B]">Приоритет</p>
                                    <p class="text-base font-semibold text-[#FF7A00]">${t.priority}</p>
                                </div>
                            </div>
                        </div>
                    `).join('');
            }
            const doneWrap = document.getElementById('p-done-tasks');
            if (doneWrap) {
                doneWrap.innerHTML = doneItems.length === 0
                    ? '<p class="text-xs text-[#6B6B6B] p-3">Выполненных задач нет</p>'
                    : doneItems.map(t => `
                        <div class="done-item">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="2.5" class="shrink-0 mt-0.5"><path d="M20 6L9 17l-5-5"/></svg>
                            <div class="flex-1 min-w-0">
                                <p class="text-sm font-medium text-[#22C55E]">Задача №${t.id}</p>
                                <p class="text-[10px] text-[#6B6B6B] truncate">${_esc(t.category_name || '—')}</p>
                            </div>
                        </div>
                    `).join('');
            }
        } catch (err) {
            console.warn('openProfile load failed:', err);
        }
    }

    function closeProfile() {
        const panel = document.getElementById('profile-panel');
        if (panel) panel.classList.remove('open');
        document.body.style.overflow = '';
    }

    function openAssignModal() { if (typeof openTaskModal === 'function') openTaskModal(); }
    function closeAssignModal() { if (typeof closeTaskModal === 'function') closeTaskModal(); }
    function submitAssign() {
        closeAssignModal();
        const toast = document.getElementById('task-toast');
        if (toast) { toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 3000); }
    }

    window.openProfile = openProfile;
    window.closeProfile = closeProfile;
    window.openAssignModal = openAssignModal;
    window.closeAssignModal = closeAssignModal;
    window.submitAssign = submitAssign;

    const taskModalEl = document.getElementById('task-modal');
    if (taskModalEl) {
        taskModalEl.addEventListener('click', e => {
            if (e.target === taskModalEl) closeAssignModal();
        });
    }
    window.setChatQuery = function (text) {
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = text;
            input.focus();
        }
    };

    window.sendChat = function () {
        const input = document.getElementById('chat-input');
        if (!input) return;
        const text = input.value.trim();
        if (!text) return;
        
        input.value = '';
        
        const toast = document.getElementById('task-toast');
        if (toast) {
            const originalText = toast.textContent;
            toast.textContent = "Сообщение успешно отправлено";
            toast.classList.remove('opacity-0', 'translate-y-[-20px]', 'pointer-events-none');
            toast.classList.add('opacity-100', 'translate-y-0');
            
            setTimeout(() => {
                toast.classList.add('opacity-0', 'translate-y-[-20px]', 'pointer-events-none');
                toast.classList.remove('opacity-100', 'translate-y-0');
                setTimeout(() => {
                    toast.textContent = originalText;
                }, 300);
            }, 2500);
        }
    };

    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                sendChat();
            }
        });
    }
});


// в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
// Подключение фронта менеджера к Django API.
// На manager_workers.html — список сотрудников (#workers-grid).
// На manager_tasks.html — список тикетов (#tasks-grid) + донат-чарт.
// в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

const TICKET_STATUS_LABELS = {
    open: 'Открыт',
    assigned: 'Назначен',
    in_progress: 'В работе',
    resolved: 'Выполнен',
    closed: 'Закрыт',
    expired: 'Просрочен',
};
TICKET_STATUS_LABELS.declined = 'Отклонена';
TICKET_STATUS_LABELS.open = 'Ожидает исполнителя';

function _esc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function _workerCard(emp) {
    const shiftDot = emp.is_on_shift ? 'bg-[#22C55E]' : 'bg-[#6B6B6B]';
    const busy = emp.is_busy
        ? `<span class="text-[#FF9A3C] text-xs">занят: ${_esc(emp.current_task_description || '—')}</span>`
        : `<span class="text-[#22C55E] text-xs">свободен</span>`;
    const role = emp.role || '';
    return `
      <div class="js-worker-card bg-[#151515] border border-white/5 rounded-[5px] p-4 flex flex-col gap-3 cursor-pointer hover:border-[#FF7A00]/40 transition-colors"
           data-emp-id="${emp.id}" data-emp-name="${_esc(emp.name)}" data-emp-role="${_esc(role)}">
        <div class="flex items-center justify-between">
          <div>
            <p class="font-semibold">${_esc(emp.name)}</p>
            <p class="text-xs text-[#6B6B6B]">${_esc(role || ('ID: ' + emp.id))}</p>
          </div>
          <span class="w-2 h-2 rounded-full ${shiftDot}" title="${emp.is_on_shift ? 'на смене' : 'не на смене'}"></span>
        </div>
        <div>${busy}</div>
        <button data-emp-id="${emp.id}" class="js-notify-btn mt-2 text-xs px-3 py-2 rounded border border-[#FF7A00] text-[#FF7A00] hover:bg-[#FF7A00]/10">
          Отправить срочное уведомление
        </button>
      </div>`;
}

async function loadWorkersGrid() {
    const grid = document.getElementById('workers-grid');
    if (!grid || !window.api || !window.api.requireAuth()) return;

    grid.innerHTML = '<p class="col-span-full text-[#6B6B6B] text-sm">Загрузка…</p>';
    try {
        const list = await window.api.get('/api/mobile/employees/');
        if (!list || list.length === 0) {
            grid.innerHTML = '<p class="col-span-full text-[#6B6B6B] text-sm">В отделе нет сотрудников</p>';
            return;
        }
        grid.innerHTML = list.map(_workerCard).join('');
        grid.querySelectorAll('.js-worker-card').forEach(card => {
            card.addEventListener('click', () => {
                if (typeof window.openProfile === 'function') {
                    window.openProfile(
                        Number(card.dataset.empId),
                        card.dataset.empName,
                        card.dataset.empRole,
                    );
                }
            });
        });
        grid.querySelectorAll('.js-notify-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.dataset.empId;
                btn.disabled = true;
                const original = btn.textContent;
                btn.textContent = 'Отправляем…';
                try {
                    await window.api.post(`/api/mobile/notify/${id}/`, {});
                    btn.textContent = 'Отправлено';
                } catch (err) {
                    btn.textContent = 'Ошибка';
                    console.error(err);
                } finally {
                    setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 2000);
                }
            });
        });
    } catch (err) {
        grid.innerHTML = `<p class="col-span-full text-red-400 text-sm">Не удалось загрузить: ${_esc(err.message || 'ошибка')}</p>`;
    }
}

function _ticketCard(t) {
    return `
      <div class="bg-[#151515] border border-white/5 rounded-[5px] p-4 flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <p class="font-semibold">Задача №${t.id}</p>
          <span class="text-xs text-[#FF9A3C]">${_esc(TICKET_STATUS_LABELS[t.status] || t.status)}</span>
        </div>
        <p class="text-sm text-[#B3B3B3]">${_esc(t.description)}</p>
        <div class="text-xs text-[#6B6B6B] flex flex-wrap gap-3">
          <span>Категория: ${_esc(t.category_name || '—')}</span>
          <span>Исполнитель: ${_esc(t.assignee_name || 'не назначен')}</span>
          <span>Приоритет: ${t.priority}</span>
        </div>
      </div>`;
}

function _renderDonut(done, total) {
    const pct = total ? Math.round(done / total * 100) : 0;
    const donutEl = document.getElementById('donut-done');
    const pctEl = document.getElementById('donut-pct');
    const legendPending = document.getElementById('legend-pending');
    const legendDone = document.getElementById('legend-done');
    if (donutEl) {
        const C = 389.6;
        donutEl.setAttribute('stroke-dashoffset', String(C - (C * pct / 100)));
    }
    if (pctEl) pctEl.textContent = `${pct}%`;
    if (legendPending) legendPending.textContent = String(Math.max(0, total - done));
    if (legendDone) legendDone.textContent = String(done);
}

async function loadTasksGrid() {
    const grid = document.getElementById('tasks-grid');
    if (!grid || !window.api || !window.api.requireAuth()) return;

    grid.innerHTML = '<p class="text-[#6B6B6B] text-sm">Загрузка…</p>';
    try {
        const list = await window.api.get('/api/mobile/tickets/');
        const tickets = list || [];

        const filterInput = document.getElementById('filter-input');
        const render = () => {
            const q = (filterInput?.value || '').toLowerCase().trim();
            const filtered = q
                ? tickets.filter(t =>
                    String(t.id).includes(q) ||
                    (t.description || '').toLowerCase().includes(q) ||
                    (t.assignee_name || '').toLowerCase().includes(q))
                : tickets;
            grid.innerHTML = filtered.length
                ? filtered.map(_ticketCard).join('')
                : '<p class="text-[#6B6B6B] text-sm">Ничего не найдено</p>';
        };

        const done = tickets.filter(t => t.status === 'resolved' || t.status === 'closed').length;
        _renderDonut(done, tickets.length);

        render();
        filterInput?.addEventListener('input', render);
    } catch (err) {
        grid.innerHTML = `<p class="text-red-400 text-sm">Не удалось загрузить: ${_esc(err.message || 'ошибка')}</p>`;
    }
}

// Плавная замена контента: показываем старое пока грузим новое, фейдим только при изменении
function _smoothReplace(el, newHtml) {
    if (!el) return;
    if (el.innerHTML.trim() === newHtml.trim()) return; // ничего не изменилось — не трогаем DOM
    el.style.transition = 'opacity 0.15s ease';
    el.style.opacity = '0';
    setTimeout(() => {
        el.innerHTML = newHtml;
        el.style.opacity = '1';
    }, 150);
}

// Живые таймеры: обновляем каждую секунду только текст, без перерисовки
function _tickActiveTimers() {
    const now = Date.now();
    document.querySelectorAll('[data-task-deadline]').forEach(el => {
        const dl = parseInt(el.dataset.taskDeadline, 10);
        const left = Math.max(0, dl - now);
        const h = String(Math.floor(left / 3600000)).padStart(2, '0');
        const m = String(Math.floor((left % 3600000) / 60000)).padStart(2, '0');
        const s = String(Math.floor((left % 60000) / 1000)).padStart(2, '0');
        el.textContent = `${h}:${m}:${s}`;
        if (left === 0) {
            el.className = el.className.replace('text-[#FF7A00]', 'text-[#EF4444]');
        }
    });
}

async function loadMgrActiveTasks() {
    const wrap = document.getElementById('mgr-active-tasks');
    if (!wrap || !window.api || !window.api.requireAuth()) return;

    const HEADER = '<h2 class="text-xl font-medium sticky top-0 bg-[#0D0D0D] pt-2 z-10">Задачи в работе</h2>';

    // Первый вызов — показываем заглушку
    if (!wrap.querySelector('[data-task-id]')) {
        wrap.innerHTML = HEADER + '<p class="text-xs text-[#6B6B6B] py-4">Загрузка…</p>';
    }

    try {
        const list = await window.api.get('/api/mobile/tickets/');
        const active = (list || []).filter(t => ['in_progress', 'assigned'].includes(t.status));

        if (active.length === 0) {
            wrap.innerHTML = HEADER + '<p class="text-xs text-[#6B6B6B] py-4">Активных задач нет</p>';
            return;
        }

        // Сравниваем текущий набор id с новым — если одинаковый, не перерисовываем
        const renderedIds = new Set(
            Array.from(wrap.querySelectorAll('[data-task-id]')).map(el => el.dataset.taskId)
        );
        const freshIds = new Set(active.map(t => String(t.id)));
        const same = renderedIds.size === freshIds.size && [...freshIds].every(id => renderedIds.has(id));
        if (same) return; // таймеры продолжают тикать сами

        // Набор задач изменился — перерисовываем
        wrap.innerHTML = HEADER + active.map(t => {
            const dlMs = t.deadline ? new Date(t.deadline).getTime() : 0;
            const left = dlMs ? Math.max(0, dlMs - Date.now()) : 0;
            const h = String(Math.floor(left / 3600000)).padStart(2, '0');
            const m = String(Math.floor((left % 3600000) / 60000)).padStart(2, '0');
            const s = String(Math.floor((left % 60000) / 1000)).padStart(2, '0');
            const timerClass = left > 0 ? 'text-[#FF7A00]' : 'text-[#EF4444]';
            const dlAttr = dlMs ? `data-task-deadline="${dlMs}"` : '';
            return `
              <div class="task-card" data-task-id="${t.id}">
                <div class="flex justify-between items-start gap-4">
                    <div>
                        <h3 class="font-semibold text-base tracking-tight">Задача №${t.id}</h3>
                        <p class="text-xs text-[#6B6B6B] mt-0.5">${_esc((t.description || '').slice(0, 80))}</p>
                        <p class="text-xs text-[#B3B3B3] mt-1">Выполняет: ${_esc(t.assignee_name || '—')}</p>
                    </div>
                    <div class="text-right shrink-0">
                        <p class="text-[10px] text-[#6B6B6B]">До конца срока выполнения:</p>
                        <p class="text-lg font-semibold ${timerClass} tracking-widest" ${dlAttr}>${h}:${m}:${s}</p>
                    </div>
                </div>
              </div>`;
        }).join('');
    } catch (_) {
        // При ошибке поллинга не затираем уже отрисованные задачи
    }
}

async function loadMgrEmployees() {
    const wrap = document.getElementById('mgr-employees-list');
    if (!wrap || !window.api || !window.api.requireAuth()) return;

    // Показываем "Загрузка…" только при первом вызове (контента ещё нет)
    const isFirst = !wrap.querySelector('.employee-row');
    if (isFirst) wrap.innerHTML = '<p class="text-xs text-[#6B6B6B] text-center p-4">Загрузка…</p>';

    try {
        const list = await window.api.get('/api/mobile/employees/');
        if (!list || list.length === 0) {
            _smoothReplace(wrap, '<p class="text-xs text-[#6B6B6B] text-center p-4">Нет сотрудников</p>');
            return;
        }
        const newHtml = list.map(e => {
            const badge = e.is_busy
                ? '<span class="badge-working"><span class="w-1.5 h-1.5 rounded-full bg-[#F59E0B] inline-block shrink-0"></span>В работе</span>'
                : (e.is_on_shift
                    ? '<span class="badge-waiting">Ожидает</span>'
                    : '<span class="badge-waiting" style="opacity:.5">Не на смене</span>');
            const initials = (e.name || '?').split(' ').map(s => s[0]).slice(0, 2).join('').toUpperCase();
            const subline = e.current_task_description
                ? `📌 ${e.current_task_description}`
                : (e.role || 'Сотрудник');
            return `
              <div class="employee-row">
                <div class="avatar">${_esc(initials)}</div>
                <div class="flex-1 min-w-0">
                    <p class="text-xs font-medium truncate">${_esc(e.name)}</p>
                    <p class="text-[10px] text-[#6B6B6B] truncate">${_esc(subline)}</p>
                </div>
                ${badge}
              </div>`;
        }).join('');
        // Обновляем DOM только если данные изменились, плавно
        _smoothReplace(wrap, newHtml);
    } catch (err) {
        if (isFirst) wrap.innerHTML = `<p class="text-xs text-red-400 text-center p-4">Ошибка: ${_esc(err.message || '')}</p>`;
        // При ошибке на фоне — не затираем уже отрисованный список
    }
}

async function loadMgrProfile() {
    if (!document.getElementById('mgr-profile-name')) return;
    if (!window.api || !window.api.requireAuth()) return;
    try {
        const data = await window.api.get('/api/profile/summary/');
        const name = data.name || '—';
        const role = data.role || (data.department ? data.department : '—');
        document.getElementById('mgr-profile-name').textContent = name;
        document.getElementById('mgr-profile-role').textContent = role;
        const avatar = document.getElementById('mgr-profile-avatar');
        if (avatar) {
            const initials = name.split(' ').map(s => s[0] || '').slice(0, 2).join('').toUpperCase();
            avatar.textContent = initials || '—';
        }
        const done = Number(data.done_week || 0);
        const total = Number(data.total_week || 0);
        const pct = total > 0 ? Math.round(done / total * 100) : 0;
        const bar = document.getElementById('mgr-profile-progress');
        if (bar) bar.style.width = pct + '%';
        const doneEl = document.getElementById('mgr-profile-done');
        if (doneEl) doneEl.textContent = String(done);
        const totalEl = document.getElementById('mgr-profile-total');
        if (totalEl) totalEl.textContent = total > 0 ? `${pct}% (из ${total})` : 'из 0';
    } catch (err) {
        console.warn('loadMgrProfile:', err);
    }
}

const _NOTIF_ICON = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="shrink-0 mt-0.5"><path d="M9 18l6-6-6-6"/></svg>`;

function _notifTimeShort(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const today = new Date();
    const sameDay = d.toDateString() === today.toDateString();
    if (sameDay) {
        return d.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('ru', { day: '2-digit', month: '2-digit' }) + ' ' +
           d.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
}

function _notifStyle(title) {
    const t = (title || '').toLowerCase();
    if (t.includes('срочн') || t.includes('критич')) {
        return { wrap: 'notif-row bg-[#EF4444]/5 border-y border-[#EF4444]', text: 'text-[#EF4444] font-medium' };
    }
    if (t.includes('просрочк') || t.includes('эскал') || t.includes('повторно')) {
        return { wrap: 'notif-row bg-[#FF7A00]/5 border-y border-[#FF7A00]', text: 'text-[#FF7A00] font-medium' };
    }
    if (t.includes('выполн') || t.includes('заверш')) {
        return { wrap: 'notif-row bg-[#22C55E]/5 border-y border-[#22C55E]', text: 'text-[#22C55E] font-medium' };
    }
    return { wrap: 'notif-row', text: 'text-white' };
}

async function loadMgrNotifications() {
    const wrap = document.getElementById('mgr-notif-list');
    if (!wrap || !window.api || !window.api.requireAuth()) return;

    // Показываем "Загрузка…" только при первом вызове
    const isFirst = !wrap.querySelector('.notif-row');
    if (isFirst) wrap.innerHTML = '<p class="text-xs text-[#6B6B6B] text-center p-4">Загрузка…</p>';

    try {
        const list = await window.api.get('/api/notifications/?limit=50');
        if (!list || list.length === 0) {
            _smoothReplace(wrap, '<p class="text-xs text-[#6B6B6B] text-center p-4">Уведомлений пока нет</p>');
            return;
        }
        const newHtml = list.map(n => {
            const st = _notifStyle(n.title);
            const text = n.message ? `${n.title}: ${n.message}` : n.title;
            return `
              <div class="${st.wrap} flex">
                ${_NOTIF_ICON}
                <div class="flex-1 min-w-0">
                  <p class="text-xs leading-snug ${st.text}">${_esc(text)}</p>
                </div>
                <span class="text-[10px] text-[#6B6B6B] shrink-0 ml-1">${_esc(_notifTimeShort(n.created_at))}</span>
              </div>`;
        }).join('');
        // Обновляем плавно только при реальных изменениях
        _smoothReplace(wrap, newHtml);
    } catch (err) {
        if (isFirst) wrap.innerHTML = `<p class="text-xs text-red-400 text-center p-4">Ошибка: ${_esc(err.message || '')}</p>`;
        // При фоновой ошибке — не стираем актуальные уведомления
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('workers-grid')) loadWorkersGrid();
    if (document.getElementById('tasks-grid')) loadTasksGrid();
    if (document.getElementById('mgr-active-tasks')) {
        loadMgrActiveTasks();
        // Живые таймеры — тикают каждую секунду
        setInterval(_tickActiveTimers, 1000);
        // Автообновление списка задач — каждые 15 секунд
        setInterval(loadMgrActiveTasks, 15000);
    }
    if (document.getElementById('mgr-employees-list')) {
        loadMgrEmployees();
        // Обновляем статусы сотрудников каждые 20 секунд
        setInterval(loadMgrEmployees, 20000);
    }
    if (document.getElementById('mgr-profile-name')) loadMgrProfile();
    if (document.getElementById('mgr-notif-list')) {
        loadMgrNotifications();
        // Новые уведомления каждые 30 секунд
        setInterval(loadMgrNotifications, 30000);
    }

    // ── Мгновенные обновления через WebSocket (если ws.js подключён) ─────────
    // При любом изменении статуса тикета — обновляем активные задачи,
    // список сотрудников, уведомления и таблицу тикетов менеджера.
    function _onWsTicketEvent() {
        if (document.getElementById('mgr-active-tasks'))   loadMgrActiveTasks();
        if (document.getElementById('mgr-employees-list')) loadMgrEmployees();
        if (document.getElementById('mgr-notif-list'))     loadMgrNotifications();
        if (document.getElementById('tasks-grid'))         loadTasksGrid();
        if (document.getElementById('workers-grid'))       loadWorkersGrid();
    }
    window.addEventListener('ws:ticket_status_changed', _onWsTicketEvent);
    window.addEventListener('ws:ticket_assigned',       _onWsTicketEvent);
});

