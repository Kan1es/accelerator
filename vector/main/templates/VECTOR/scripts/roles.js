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