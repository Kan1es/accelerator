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

    // ===== КАЛЕНДАРЬ =====
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
                ? 'text-[#CC6200] font-[800] bg-[#CC6200]/10 rounded-sm' // Выделение сегодня
                : 'p-1 hover:text-white cursor-pointer transition-colors';
            grid.appendChild(span);
        }
    }

    // Глобальные функции для кнопок календаря
    window.changeMonth = (n) => {
        viewDate.setMonth(viewDate.getMonth() + n);
        renderCalendar();
    };

    renderCalendar();
});

// ===== ГЛОБАЛЬНЫЕ ФУНКЦИИ УПРАВЛЕНИЯ =====

// Установка текста в инпут чата
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