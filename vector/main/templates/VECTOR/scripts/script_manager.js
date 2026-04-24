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
    const workers = [
        { id:1, name:'Имя Фамилия', role:'Должность', progress:74, activeTasks:[
            { id:'153', title:'Проверка телефонной связи', status:'В работе', timer:'02:34:55' },
            { id:'154', title:'Замена кабеля в серверной', status:'В работе', timer:'01:10:20' },
            { id:'154', title:'Замена кабеля в серверной', status:'В работе', timer:'01:10:20' },
            { id:'154', title:'Замена кабеля в серверной', status:'В работе', timer:'01:10:20' },
            { id:'154', title:'Замена кабеля в серверной', status:'В работе', timer:'01:10:20' },
            { id:'154', title:'Замена кабеля в серверной', status:'В работе', timer:'01:10:20' },
            { id:'154', title:'Замена кабеля в серверной', status:'В работе', timer:'01:10:20' }

        ], upcomingTasks:[
            { id:'163', title:'Проверка телефонной связи', timer:'02:34:55' },
            { id:'164', title:'Инвентаризация склада', timer:'05:00:00' },
            { id:'165', title:'Техническое обслуживание', timer:'03:45:00' },
            { id:'166', title:'Проверка сети', timer:'01:20:00' },
            { id:'167', title:'Замена оборудования', timer:'04:10:00' },
            { id:'168', title:'Отчёт по выполнению', timer:'06:00:00' },
            { id:'168', title:'Отчёт по выполнению', timer:'06:00:00' },
            { id:'168', title:'Отчёт по выполнению', timer:'06:00:00' },
            { id:'168', title:'Отчёт по выполнению', timer:'06:00:00' },
            { id:'168', title:'Отчёт по выполнению', timer:'06:00:00' }

        ], doneTasks:[
            { date:'22 марта', items:[
                { id:'52', title:'Задача №52', desc:'Пример выполненной задачи', time:'13:52' },
                { id:'52b', title:'Задача №52', desc:'Пример выполненной задачи', time:'13:52' },
                { id:'52c', title:'Задача №52', desc:'Пример выполненной задачи', time:'13:52' },
                { id:'52d', title:'Задача №52', desc:'Пример выполненной задачи', time:'13:52' },
                { id:'52e', title:'Задача №52', desc:'Пример выполненной задачи', time:'13:52' },
                { id:'52f', title:'Задача №52', desc:'Пример выполненной задачи', time:'13:52' }
            ]}
        ]},
        { id:2, name:'Имя Фамилия', role:'Должность', progress:55, activeTasks:[
            { id:'155', title:'Настройка Wi-Fi точек', status:'В работе', timer:'00:45:00' }
        ], upcomingTasks:[
            { id:'169', title:'Калибровка датчиков', timer:'02:00:00' },
            { id:'170', title:'Замена ламп в цехе', timer:'03:30:00' },
            { id:'171', title:'Проверка вентиляции', timer:'05:15:00' }
        ], doneTasks:[
            { date:'21 марта', items:[
                { id:'48', title:'Задача №48', desc:'Пример выполненной задачи', time:'10:15' },
                { id:'49', title:'Задача №49', desc:'Пример выполненной задачи', time:'11:30' },
                { id:'50', title:'Задача №50', desc:'Пример выполненной задачи', time:'14:00' }
            ]}
        ]},
        { id:3, name:'Имя Фамилия', role:'Должность', progress:88, activeTasks:[
            { id:'156', title:'Замена оборудования', status:'В работе', timer:'01:55:30' }
        ], upcomingTasks:[
            { id:'172', title:'Аудит серверной комнаты', timer:'01:10:00' },
            { id:'173', title:'Проверка пожарных датчиков', timer:'02:40:00' }
        ], doneTasks:[
            { date:'22 марта', items:[
                { id:'60', title:'Задача №60', desc:'Пример выполненной задачи', time:'09:45' },
                { id:'61', title:'Задача №61', desc:'Пример выполненной задачи', time:'12:20' },
                { id:'62', title:'Задача №62', desc:'Пример выполненной задачи', time:'15:05' },
                { id:'63', title:'Задача №63', desc:'Пример выполненной задачи', time:'17:30' }
            ]}
        ]},
        { id:4, name:'Имя Фамилия', role:'Должность', progress:42, activeTasks:[
            { id:'157', title:'Сортировка товара на ленте', status:'В работе', timer:'03:20:00' }
        ], upcomingTasks:[
            { id:'174', title:'Обслуживание склада', timer:'04:50:00' },
            { id:'175', title:'Перемещение стеллажей', timer:'02:25:00' },
            { id:'176', title:'Проверка маркировки', timer:'01:45:00' }
        ], doneTasks:[
            { date:'20 марта', items:[
                { id:'40', title:'Задача №40', desc:'Пример выполненной задачи', time:'08:30' },
                { id:'41', title:'Задача №41', desc:'Пример выполненной задачи', time:'11:00' }
            ]}
        ]},
        { id:5, name:'Имя Фамилия', role:'Должность', progress:60, activeTasks:[
            { id:'158', title:'Проверка кассовых аппаратов', status:'В работе', timer:'00:30:00' }
        ], upcomingTasks:[
            { id:'177', title:'Отчёт за неделю', timer:'06:30:00' }
        ], doneTasks:[
            { date:'22 марта', items:[
                { id:'70', title:'Задача №70', desc:'Пример выполненной задачи', time:'10:00' },
                { id:'71', title:'Задача №71', desc:'Пример выполненной задачи', time:'13:15' }
            ]}
        ]},
        { id:6, name:'Имя Фамилия', role:'Должность', progress:77, activeTasks:[
            { id:'159', title:'Инвентаризация товаров', status:'В работе', timer:'02:10:00' }
        ], upcomingTasks:[
            { id:'178', title:'Разгрузка фуры', timer:'03:00:00' },
            { id:'179', title:'Проверка весового оборудования', timer:'01:30:00' }
        ], doneTasks:[
            { date:'21 марта', items:[
                { id:'75', title:'Задача №75', desc:'Пример выполненной задачи', time:'09:00' },
                { id:'76', title:'Задача №76', desc:'Пример выполненной задачи', time:'12:00' },
                { id:'77', title:'Задача №77', desc:'Пример выполненной задачи', time:'15:00' }
            ]}
        ]},
        { id:7, name:'Имя Фамилия', role:'Должность', progress:33, activeTasks:[
            { id:'160', title:'Обслуживание холодильников', status:'В работе', timer:'01:40:00' }
        ], upcomingTasks:[
            { id:'180', title:'Ремонт холодильной камеры', timer:'05:00:00' }
        ], doneTasks:[
            { date:'19 марта', items:[
                { id:'80', title:'Задача №80', desc:'Пример выполненной задачи', time:'14:00' }
            ]}
        ]},
        { id:8, name:'Имя Фамилия', role:'Должность', progress:91, activeTasks:[
            { id:'161', title:'Проверка охранных систем', status:'В работе', timer:'00:55:00' }
        ], upcomingTasks:[
            { id:'181', title:'Настройка камер видеонаблюдения', timer:'02:20:00' },
            { id:'182', title:'Тест сигнализации', timer:'01:05:00' }
        ], doneTasks:[
            { date:'22 марта', items:[
                { id:'85', title:'Задача №85', desc:'Пример выполненной задачи', time:'08:50' },
                { id:'86', title:'Задача №86', desc:'Пример выполненной задачи', time:'11:40' },
                { id:'87', title:'Задача №87', desc:'Пример выполненной задачи', time:'14:55' },
                { id:'88', title:'Задача №88', desc:'Пример выполненной задачи', time:'17:10' },
                { id:'89', title:'Задача №89', desc:'Пример выполненной задачи', time:'18:30' }
            ]}
        ]},
        { id:9, name:'Имя Фамилия', role:'Должность', progress:50, activeTasks:[
            { id:'162', title:'Заправка картриджей', status:'В работе', timer:'00:25:00' }
        ], upcomingTasks:[
            { id:'183', title:'Замена принтеров', timer:'03:10:00' }
        ], doneTasks:[
            { date:'20 марта', items:[
                { id:'90', title:'Задача №90', desc:'Пример выполненной задачи', time:'10:30' }
            ]}
        ]},
        { id:10, name:'Имя Фамилия', role:'Должность', progress:68, activeTasks:[
            { id:'163', title:'Уборка производственного цеха', status:'В работе', timer:'01:15:00' }
        ], upcomingTasks:[
            { id:'184', title:'Дезинфекция помещений', timer:'02:45:00' },
            { id:'185', title:'Проверка чистоты зон', timer:'01:00:00' }
        ], doneTasks:[
            { date:'21 марта', items:[
                { id:'95', title:'Задача №95', desc:'Пример выполненной задачи', time:'09:30' },
                { id:'96', title:'Задача №96', desc:'Пример выполненной задачи', time:'13:00' }
            ]}
        ]},
        { id:11, name:'Имя Фамилия', role:'Должность', progress:82, activeTasks:[
            { id:'164', title:'Выкладка товаров', status:'В работе', timer:'02:50:00' }
        ], upcomingTasks:[
            { id:'186', title:'Ротация товаров', timer:'04:00:00' },
            { id:'187', title:'Обновление ценников', timer:'01:50:00' }
        ], doneTasks:[
            { date:'22 марта', items:[
                { id:'100', title:'Задача №100', desc:'Пример выполненной задачи', time:'10:10' },
                { id:'101', title:'Задача №101', desc:'Пример выполненной задачи', time:'12:40' },
                { id:'102', title:'Задача №102', desc:'Пример выполненной задачи', time:'15:20' }
            ]}
        ]},
        { id:12, name:'Имя Фамилия', role:'Должность', progress:47, activeTasks:[
            { id:'165', title:'Разгрузка поставки', status:'В работе', timer:'03:05:00' }
        ], upcomingTasks:[
            { id:'188', title:'Приёмка товара', timer:'02:00:00' }
        ], doneTasks:[
            { date:'18 марта', items:[
                { id:'105', title:'Задача №105', desc:'Пример выполненной задачи', time:'11:00' },
                { id:'106', title:'Задача №106', desc:'Пример выполненной задачи', time:'14:30' }
            ]}
        ]}
    ];

    // ─── RENDER WORKERS GRID ────────────────────────────────────
    const grid = document.getElementById('workers-grid');

    workers.forEach(w => {
        const task = w.activeTasks[0];
        const card = document.createElement('div');
        card.className = 'worker-card';
        card.onclick = () => openProfile(w.id);
        card.innerHTML = `
            <div class="flex items-center gap-3 mb-3">
                <div class="avatar">ФОТО</div>
                <div>
                    <p class="font-semibold text-sm">${w.name}</p>
                    <p class="text-[11px] text-[#6B6B6B]">${w.role}</p>
                </div>
            </div>
            <div class="space-y-1 text-xs mb-4">
                <p><span class="text-[#6B6B6B]">Занятость: </span><span class="text-[#F59E0B]">В работе</span></p>
                <p><span class="text-[#6B6B6B]">Задача: </span><span class="text-white">№${task ? task.id : '—'}</span></p>
                ${task ? `<p class="text-[#6B6B6B] text-[10px] truncate">${task.title}</p>` : ''}
            </div>
            <button class="w-full py-1.5 text-xs border border-white/10 rounded-[5px] hover:border-[#FF7A00]/40 hover:text-[#FF7A00] transition-colors">
                Подробнее
            </button>
        `;
        grid.appendChild(card);
    });

    // ─── PROFILE OPEN/CLOSE ─────────────────────────────────────
    let currentWorker = null;

    function openProfile(id) {
        const w = workers.find(x => x.id === id);
        if (!w) return;
        currentWorker = w;

        // Fill header info
        document.getElementById('p-name').textContent = w.name;
        document.getElementById('p-role').textContent = w.role;
        document.getElementById('p-progress').style.width = w.progress + '%';
        document.getElementById('p-percent').textContent = w.progress + '%';

        // Update chat pill
        const firstTask = w.activeTasks[0];
        if (firstTask) {
            document.getElementById('pill-task').textContent = `Какой срок выполнения задачи №${firstTask.id}?`;
        }

        // Active tasks
        const activeEl = document.getElementById('p-active-tasks');
        activeEl.innerHTML = '';
        w.activeTasks.forEach(t => {
            activeEl.innerHTML += `
                <div class="task-card-sm flex justify-between items-center gap-4">
                    <div>
                        <h3 class="font-semibold text-sm">Задача №${t.id}</h3>
                        <p class="text-[11px] text-[#6B6B6B]">${t.title}</p>
                    </div>
                    <span class="badge-working shrink-0"><span class="w-1.5 h-1.5 rounded-full bg-[#F59E0B] inline-block"></span>${t.status}</span>
                </div>
            `;
        });

        // Upcoming tasks
        const upEl = document.getElementById('p-upcoming-tasks');
        upEl.innerHTML = '';
        w.upcomingTasks.forEach(t => {
            upEl.innerHTML += `
                <div class="task-card-sm">
                    <div class="flex justify-between items-start gap-4">
                        <div>
                            <h3 class="font-semibold text-sm">Задача №${t.id}</h3>
                            <p class="text-[11px] text-[#6B6B6B]">${t.title}</p>
                        </div>
                        <div class="text-right shrink-0">
                            <p class="text-[10px] text-[#6B6B6B]">До конца срока выполнения:</p>
                            <p class="text-base font-semibold text-[#EF4444] tracking-widest task-timer" data-time="${t.timer}">${t.timer}</p>
                        </div>
                    </div>
                </div>
            `;
        });

        // Done tasks
        const doneEl = document.getElementById('p-done-tasks');
        doneEl.innerHTML = '';
        w.doneTasks.forEach(group => {
            doneEl.innerHTML += `<p class="date-group-label">${group.date}</p>`;
            group.items.forEach(item => {
                doneEl.innerHTML += `
                    <div class="done-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="2.5" class="shrink-0 mt-0.5"><path d="M20 6L9 17l-5-5"/></svg>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-[#22C55E]">${item.title}</p>
                            <p class="text-[10px] text-[#6B6B6B] truncate">${item.desc}</p>
                        </div>
                        <span class="text-[10px] text-[#6B6B6B] shrink-0">${item.time}</span>
                    </div>
                `;
            });
        });

        // Start timers
        startTimers();

        // Open panel
        document.getElementById('profile-panel').classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeProfile() {
        document.getElementById('profile-panel').classList.remove('open');
        document.body.style.overflow = '';
    }

    // ─── TIMERS ─────────────────────────────────────────────────
    let timerInterval = null;

    function startTimers() {
        if (timerInterval) clearInterval(timerInterval);
        const timers = document.querySelectorAll('.task-timer');
        const data = Array.from(timers).map(el => {
            const parts = el.dataset.time.split(':').map(Number);
            return { el, secs: parts[0]*3600 + parts[1]*60 + parts[2] };
        });
        timerInterval = setInterval(() => {
            data.forEach(t => {
                if (t.secs > 0) t.secs--;
                const h = String(Math.floor(t.secs/3600)).padStart(2,'0');
                const m = String(Math.floor((t.secs%3600)/60)).padStart(2,'0');
                const s = String(t.secs%60).padStart(2,'0');
                t.el.textContent = `${h}:${m}:${s}`;
            });
        }, 1000);
    }

    // ─── ASSIGN MODAL ───────────────────────────────────────────
    function openAssignModal() {
        openTaskModal();
    }
    function closeAssignModal() {
        closeTaskModal();
    }
    function submitAssign() {
        closeAssignModal();
        const toast = document.getElementById('task-toast');
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }
    document.getElementById('task-modal').addEventListener('click', e => {
        if (e.target === document.getElementById('task-modal')) closeAssignModal();
    });
    window.setChatQuery = function (text) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = text;
        input.focus();
    }
};

        
