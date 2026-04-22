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

    function startShift() {
        shiftStarted = true;

        shiftToggleText.textContent = 'Закончить смену';
        shiftIndicator.classList.remove('bg-[#22C55E]');
        shiftIndicator.classList.add('bg-[#EF4444]');
        shiftToggleBtn.querySelector('p').textContent = 'Смена активна';

        startShiftTimer();
    }

    function endShift() {
        shiftStarted = false;

        shiftToggleText.textContent = 'Начать смену';
        shiftIndicator.classList.remove('bg-[#EF4444]');
        shiftIndicator.classList.add('bg-[#22C55E]');
        shiftToggleBtn.querySelector('p').textContent = 'Статус';

        stopShiftTimer();
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

    shiftConfirmBtn?.addEventListener('click', () => {
        if (confirmStep === 1) {
            openShiftModal(2);
            return;
        }

        endShift();
        closeShiftModal();
    });
    function formatShiftDuration(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
        const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
        const seconds = String(totalSeconds % 60).padStart(2, '0');

        return `${hours}:${minutes}:${seconds}`;
    }

    function startShiftTimer() {
        if (!shiftTimer || !shiftTimerWrap) return;

        shiftStartTime = new Date();
        shiftTimerWrap.classList.remove('hidden');
        shiftTimer.textContent = '00:00:00';

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
function taskManager() {
    return {
        search: '',
        filter: 'all',
        showConfirm: false,
        pendingTaskId: null, // Храним ID вместо индекса для надежности
        tasks: [
            { id: 31, title: 'Замена оборудования', dept: 'Отдел I, цех 2', status: 'assigned', deadline: '14:00' },
            { id: 153, title: 'Проверка связи', dept: 'Отдел I, цех 4', status: 'progress', deadline: '15:00' },
            { id: 204, title: 'Плановый обход', dept: 'Цех 5', status: 'done', deadline: '18:00' },
            { id: 201, title: 'Плановый обход', dept: 'Цех 5', status: 'progress', deadline: '18:00' }
        ],
        meetings: [
            { id: 1, title: 'Встреча с менеджером', comment: 'Разбор правок по цеху №2', time: '19:00' },
            { id: 2, title: 'Инструктаж', comment: 'Техника безопасности', time: '17:30' }
        ],

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
            const h = Math.floor(diffMins / 6000);
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

        // Передаем ID задачи, а не индекс
        changeStatus(id) {
            const task = this.tasks.find(t => t.id === id);
            if (!task) return;

            if (task.status === 'assigned') {
                task.status = 'progress';
            } else if (task.status === 'progress') {
                this.pendingTaskId = id;
                this.showConfirm = true; // Открываем окно
            }
        },

        confirmDone() {
            const task = this.tasks.find(t => t.id === this.pendingTaskId);
            if (task) {
                task.status = 'done';
            }
            this.showConfirm = false;
            this.pendingTaskId = null;
        },

        cancelDone() {
            this.showConfirm = false;
            this.pendingTaskId = null;
        }
    }
}

// Логика чата технической поддержки
function supportChat() {
    return {
        userInput: '',
        showInitialButtons: true,
        messages: [],

        // Инициализация (если нужно что-то сделать при загрузке)
        init() {
            console.log("Чат поддержки ВЕКТОР готов");
        },

        // 1. Соединение с оператором
        connectOperator() {
            this.showInitialButtons = false;
            this.addMessage('user', 'Нет, соедини меня с оператором');

            // Имитируем небольшую задержку ответа
            setTimeout(() => {
                this.addMessage('bot', 'Хорошо, уже позвал сотрудника технической поддержки. Пожалуйста, ожидайте ответа в этом чате.');
            }, 800);
        },

        // 2. Попытка через ИИ (заготовка под твою нейронку)
        tryAI() {
            this.showInitialButtons = false;
            this.addMessage('user', 'Да, давай попробуем');

            setTimeout(() => {
                this.addMessage('bot', 'Делаю запрос к интеллектуальной системе "ВЕКТОР-ИИ"...');

                // ТУТ БУДЕТ ТВОЙ FETCH К API
                setTimeout(() => {
                    this.addMessage('bot', 'Ошибка: API-ключ не найден. Система ИИ временно недоступна. Пожалуйста, введите ваш вопрос вручную для оператора.');
                }, 1500);
            }, 800);
        },

        // 3. Отправка сообщения пользователем
        sendMessage() {
            const text = this.userInput.trim();
            if (text === '') return;

            this.addMessage('user', text);
            this.userInput = '';
            this.showInitialButtons = false;

            // Здесь можно добавить проверку: если ИИ подключен — слать запрос ему, 
            // если нет — просто уведомление об ожидании оператора.
            setTimeout(() => {
                if (this.messages.length > 5 && !this.aiActive) {
                    this.addMessage('bot', 'Оператор получил ваше сообщение и ответит в течение нескольких минут.');
                }
            }, 1000);
        },

        // Вспомогательная функция добавления сообщения и автоскролла
        addMessage(role, text) {
            this.messages.push({
                id: Date.now(),
                role: role, // 'user' или 'bot'
                text: text
            });

            // Автоскролл вниз после рендеринга нового сообщения
            this.$nextTick(() => {
                const chatWin = document.getElementById('chat-window');
                if (chatWin) {
                    chatWin.scrollTo({ top: chatWin.scrollHeight, behavior: 'smooth' });
                }
            });
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