document.addEventListener('DOMContentLoaded', function() {
      // Показываем/скрываем поле "Другое" при выборе соответствующего варианта
      const expertiseSelect = document.getElementById('expertise');
      const otherFieldContainer = document.getElementById('otherFieldContainer');
      
      expertiseSelect.addEventListener('change', function() {
        if (this.value === 'other') {
          otherFieldContainer.style.display = 'block';
        } else {
          otherFieldContainer.style.display = 'none';
        }
      });

      // Обработка отправки формы
      const form = document.getElementById('expertApplicationForm');
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Собираем данные формы
        const formData = {
          fullName: document.getElementById('user-fullname').textContent,
          company: document.getElementById('company').value,
          position: document.getElementById('position').value,
          expertise: document.getElementById('expertise').value,
          otherExpertise: document.getElementById('otherExpertise').value,
          experience: document.getElementById('experience').value,
          description: document.getElementById('description').value
        };

        // Здесь можно добавить отправку данных на сервер
        console.log('Отправка данных:', formData);
        
        // Показываем уведомление об успешной отправке
        alert('Ваша заявка успешно отправлена! Мы рассмотрим её в ближайшее время.');
        form.reset();
      });
    });