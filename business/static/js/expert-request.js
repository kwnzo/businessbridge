document.addEventListener('DOMContentLoaded', function() {
  // Создаем модальное окно (аналогично registration-fields.js)
  const modal = document.createElement('div');
  modal.className = 'custom-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-body">
        <p id="modal-message"></p>
      </div>
      <div class="modal-footer">
        <button class="modal-close-btn">OK</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  // Функции для работы с модальным окном
  function showModal(message) {
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = message;
    modal.style.display = 'flex';
  }

  function closeModal() {
    modal.style.display = 'none';
  }

  // Обработчик закрытия модалки
  document.querySelector('.modal-close-btn').addEventListener('click', closeModal);
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeModal();
    }
  });

  const expertiseSelect = document.getElementById('expertise');
  const otherFieldContainer = document.getElementById('otherFieldContainer');
  
  expertiseSelect.addEventListener('change', function() {
    otherFieldContainer.style.display = this.value === 'other' ? 'block' : 'none';
  });

  const form = document.getElementById('expertApplicationForm');
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    
    const formData = {
        company: document.getElementById('company').value,
        position: document.getElementById('position').value,
        expertise: document.getElementById('expertise').value,
        experience: parseInt(document.getElementById('experience').value),
        description: document.getElementById('description').value,
        otherExpertise: document.getElementById('otherExpertise').value,
    };

    try {
        const response = await fetch('/expert-request', {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(formData)
        });

        // Обработка HTML-ответа как ошибки
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Invalid response: ${text.slice(0, 100)}`);
        }

        const data = await response.json();
      
        if (!response.ok) {
            throw new Error(data.message || 'Ошибка сервера');
        }

        if (data.success) {
            // Показываем модальное окно с сообщением об успехе
            showModal('Ваша заявка успешно отправлена! Мы рассмотрим её в ближайшее время.');
            
            // Обработчик кнопки OK в модалке
            document.querySelector('.modal-close-btn').onclick = function() {
                closeModal();
                if (data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    window.location.href = '/'; // Перенаправление на главную страницу
                }
            };
        } else {
            showModal(data.message || 'Произошла ошибка');
        }

    } catch (error) {
        showModal(error.message || 'Ошибка соединения');
    }
  });
});