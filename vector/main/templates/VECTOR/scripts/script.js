// 1. Печатная машинка
const twElement = document.getElementById('typewriter');
if (twElement) {
    const text = "олучи помощь в одну секунду";
    let i = 0;
    function type() {
        if (i < text.length) {
            twElement.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, 100);
        } else {
            
            setTimeout(() => { twElement.innerHTML = ""; i = 0; type(); }, 7000);
        }
    }
    type();
}


// 1. Управление сайдбаром
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const openBtn = document.getElementById('sidebar-open');
    
    sidebar.classList.toggle('collapsed');
    
    // Если сайдбар свернут, показываем кнопку открытия в хедере
    if (sidebar.classList.contains('collapsed')) {
        openBtn.style.display = 'block';
    } else {
        openBtn.style.display = 'none';
    }
}

// 2. Обработка вопроса с главной страницы
window.addEventListener('DOMContentLoaded', () => {
    // Ищем параметр ?query= в ссылке
    const urlParams = new URLSearchParams(window.location.search);
    const queryText = urlParams.get('query');
    
    if (queryText) {
        const input = document.getElementById('user-input');
        // Декодируем текст из URL и вставляем в поле
        input.value = decodeURIComponent(queryText);
        
        // Фокусируемся на поле, чтобы пользователь мог сразу нажать Enter
        input.focus();
    }
});



// Закрытие при клике на область чата (только для мобилок)
const mainElement = document.querySelector('main');
if (mainElement) {
    mainElement.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        if (sidebar && window.innerWidth < 1024 && !sidebar.classList.contains('sidebar-hidden')) {
            toggleSidebar();
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Печатная машинка
    const text = "Здравствуйте, выберите свою роль";
    const target = document.getElementById("tw-role");
    let i = 0;

    function type() {
        if (target && i < text.length) {
            target.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, 60);
        }
    }
    if (target) {
        type();
    }

    // Подсветка стрелок
    const emp = document.getElementById('card-emp');
    const mgr = document.getElementById('card-mgr');
    const toEmp = document.getElementById('arrow-to-emp');
    const toMgr = document.getElementById('arrow-to-mgr');

    if (emp && toEmp) {
        // Наведение на левую карточку (Сотрудник) -> стрелка влево
        emp.addEventListener('mouseenter', () => {
            toEmp.style.color = '#FF9A3C';
            toEmp.style.filter = 'drop-shadow(0 0 10px rgba(255,154,60,0.5))';
        });
        emp.addEventListener('mouseleave', () => {
            toEmp.style.color = '#2A2A2A';
            toEmp.style.filter = 'none';
        });
    }

    if (mgr && toMgr) {
        // Наведение на правую карточку (Управляющий) -> стрелка вправо
        mgr.addEventListener('mouseenter', () => {
            toMgr.style.color = '#FF9A3C';
            toMgr.style.filter = 'drop-shadow(0 0 10px rgba(255,154,60,0.5))';
        });
        mgr.addEventListener('mouseleave', () => {
            toMgr.style.color = '#2A2A2A';
            toMgr.style.filter = 'none';
        });
    }

    // Приветственное сообщение в чате
    const chatBox = document.getElementById('chat-box');
    if (chatBox && chatBox.children.length === 0) {
        addBotMessage("Здравствуйте! Я интеллектуальная система поддержки «ВЕКТОР-ИИ». Опишите вашу проблему, и я классифицирую обращение, назначу исполнителя и отправлю задачу в нужный отдел.");
    }

    // Обработка Enter в чате
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});

// Функции для чата
window.addBotMessage = function(text) {
    const chatBox = document.getElementById('chat-box');
    if (!chatBox) return;

    const botMessageHTML = `
        <div class="flex gap-4 md:gap-6 animate-gentle self-start max-w-[80%]">
            <div class="w-10 h-10 md:w-12 md:h-12 shrink-0 bg-[#151515] border border-[#2A2A2A] rounded-xl flex items-center justify-center">
                <img src="images/ВЕКТОР.svg" class="w-6 h-6 md:w-8 md:h-8">
            </div>
            <div class="space-y-2">
                <p class="text-sm text-[#FF7A00] font-semibold">ВЕКТОР</p>
                <div class="bg-[#151515] border border-[#2A2A2A] p-4 rounded-[20px] rounded-tl-none text-sm md:text-md leading-relaxed text-white">
                    ${text}
                </div>
            </div>
        </div>
    `;
    chatBox.insertAdjacentHTML('beforeend', botMessageHTML);
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
}

window.addUserMessage = function(text) {
    const chatBox = document.getElementById('chat-box');
    if (!chatBox) return;

    const userMessageHTML = `
        <div class="flex gap-4 md:gap-6 animate-gentle self-end justify-end max-w-[80%]">
            <div class="space-y-2 text-right">
                <p class="text-sm text-[#6B6B6B] font-semibold">Вы</p>
                <div class="bg-[#FF7A00]/10 border border-[#FF7A00]/30 p-4 rounded-[20px] rounded-tr-none text-sm md:text-md leading-relaxed text-white">
                    ${text}
                </div>
            </div>
        </div>
    `;
    chatBox.insertAdjacentHTML('beforeend', userMessageHTML);
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
}

window.sendMessage = async function() {
    const input = document.getElementById('user-input');
    if (!input) return;

    const text = input.value.trim();
    if (!text) return;

    addUserMessage(text);
    input.value = '';

    if (!window.api || !window.api.getToken()) {
        addBotMessage('Для отправки обращения необходимо <a href="/login.html" class="underline text-[#FF7A00]">войти</a>.');
        return;
    }

    addBotMessage('Анализирую обращение…');

    try {
        const data = await window.api.post('/api/agent/classify/', { text });
        const confidencePct = Math.round((data.confidence || 0) * 100);
        addBotMessage(
            `Заявка №${data.ticket_id} создана.<br>` +
            `Категория: <span class="text-[#FF7A00]">${data.category}</span> ` +
            `(уверенность ${confidencePct}%).<br>` +
            `Передал её в работу — отслеживайте статус в личном кабинете.`
        );
    } catch (err) {
        if (err.isTimeout) {
            addBotMessage('Сервер не ответил вовремя. Попробуйте ещё раз чуть позже.');
        } else if (err.isNetwork) {
            addBotMessage('Не удалось связаться с сервером. Проверьте соединение.');
        } else if (err.status === 503) {
            addBotMessage('ML-сервис временно недоступен. Заявка не создана.');
        } else if (err.status === 400) {
            addBotMessage(err.message || 'Текст обращения не принят.');
        } else if (err.status === 401) {
            // api.js уже редиректит на /login.html
        } else {
            addBotMessage(`Ошибка при отправке: ${err.message || 'неизвестно'}`);
        }
    }
}


