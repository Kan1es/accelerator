document.addEventListener('DOMContentLoaded', () => {

    // ===== CHAT TOGGLE =====
    const toggle = document.getElementById('chat-toggle');
    const body = document.getElementById('chat-body');
    const input = document.getElementById('chat-input-wrap');
    const chat = document.getElementById('chat');

    let collapsed = false;

    toggle.addEventListener('click', () => {
        collapsed = !collapsed;

        body.classList.toggle('hidden');
        input.classList.toggle('hidden');

        chat.classList.toggle('flex-[6]');
        chat.classList.toggle('flex-[1]');

        toggle.style.transform = collapsed ? 'rotate(180deg)' : 'rotate(0deg)';
    });
});
window.setChatQuery = function (text) {
    const input = document.getElementById('chat-input');
    if (!input) return;

    input.value = text;
    input.focus();
};

// ===== CALENDAR =====
document.addEventListener('DOMContentLoaded', () => {
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
                ? 'text-[#FF7A00] font-[800]'
                : 'p-1 hover:text-white cursor-pointer transition-colors';
            grid.appendChild(span);
        }
    }

    window.changeMonth = (n) => {
        viewDate.setMonth(viewDate.getMonth() + n);
        renderCalendar();
    };

    window.setChatQuery = (text) => {
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = text;
            input.focus();
        }
    };

    renderCalendar();
});
