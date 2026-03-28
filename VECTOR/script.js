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

// 2. Сворачивание сайдбара
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const body = document.body;

    // Переключаем класс активного состояния
    sidebar.classList.toggle('sidebar-hidden');
    
    // Блокируем скролл на фоне, когда открыто меню на мобилке
    if (window.innerWidth < 1024) {
        if (!sidebar.classList.contains('sidebar-hidden')) {
            body.style.overflow = 'hidden';
        } else {
            body.style.overflow = '';
        }
    }
}

// Закрытие при клике на область чата (только для мобилок)
document.querySelector('main').addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    if (window.innerWidth < 1024 && !sidebar.classList.contains('sidebar-hidden')) {
        toggleSidebar();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    // Печатная машинка
    const text = "Здравствуйте, выберите свою роль";
    const target = document.getElementById("tw-role");
    let i = 0;

    function type() {
        if (i < text.length) {
            target.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, 60);
        }
    }
    type();

    // Подсветка стрелок
    const emp = document.getElementById('card-emp');
    const mgr = document.getElementById('card-mgr');
    const toEmp = document.getElementById('arrow-to-emp');
    const toMgr = document.getElementById('arrow-to-mgr');

    // Наведение на левую карточку (Сотрудник) -> стрелка влево
    emp.addEventListener('mouseenter', () => {
        toEmp.style.color = '#FF9A3C';
        toEmp.style.filter = 'drop-shadow(0 0 10px rgba(255,154,60,0.5))';
    });
    emp.addEventListener('mouseleave', () => {
        toEmp.style.color = '#2A2A2A';
        toEmp.style.filter = 'none';
    });

    // Наведение на правую карточку (Управляющий) -> стрелка вправо
    mgr.addEventListener('mouseenter', () => {
        toMgr.style.color = '#FF9A3C';
        toMgr.style.filter = 'drop-shadow(0 0 10px rgba(255,154,60,0.5))';
    });
    mgr.addEventListener('mouseleave', () => {
        toMgr.style.color = '#2A2A2A';
        toMgr.style.filter = 'none';
    });
});