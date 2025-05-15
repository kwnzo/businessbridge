// Функция для переключения видимости статей
    function toggleArticles(el) {
      if (event.target.closest('.scroll-btn, .article-card')) return;
      
      el.classList.toggle("expanded");
      if (el.classList.contains("expanded")) {
        updateArrowVisibility(el);
      }
    }

    // Функция для прокрутки статей
    function scrollArticles(button, amount) {
      event.stopPropagation();
      const scrollContainer = button.parentElement.querySelector('.articles-scroll');
      scrollContainer.scrollBy({
        left: amount,
        behavior: 'smooth'
      });
      
      // Обновляем стрелки после прокрутки
      setTimeout(() => updateArrowVisibility(button.closest('.expert')), 300);
    }

    // Функция для обновления видимости стрелок
    function updateArrowVisibility(expertElement) {
      const scrollContainer = expertElement.querySelector('.articles-scroll');
      const leftBtn = expertElement.querySelector('.scroll-btn.left');
      const rightBtn = expertElement.querySelector('.scroll-btn.right');
      
      // Проверяем позицию прокрутки
      const isAtStart = scrollContainer.scrollLeft <= 10;
      const isAtEnd = scrollContainer.scrollLeft + scrollContainer.clientWidth >= scrollContainer.scrollWidth - 10;
      
      // Обновляем видимость стрелок
      leftBtn.classList.toggle('hidden', isAtStart);
      rightBtn.classList.toggle('hidden', isAtEnd);
    }

    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
      document.querySelectorAll('.expert').forEach(expert => {
        const scrollContainer = expert.querySelector('.articles-scroll');
        
        // Наблюдаем за изменениями прокрутки
        scrollContainer.addEventListener('scroll', function() {
          updateArrowVisibility(expert);
        });
        
        // Проверяем видимость стрелок при загрузке
        if (expert.classList.contains('expanded')) {
          updateArrowVisibility(expert);
        }
        
        // Обновляем при изменении размера окна
        window.addEventListener('resize', () => {
          if (expert.classList.contains('expanded')) {
            updateArrowVisibility(expert);
          }
        });
      });
    });