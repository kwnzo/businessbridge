document.addEventListener('DOMContentLoaded', function() {
  const expertiseSelect = document.getElementById('expertise');
  const otherFieldContainer = document.getElementById('otherFieldContainer');
  
  expertiseSelect.addEventListener('change', function() {
    otherFieldContainer.style.display = this.value === 'other' ? 'block' : 'none';
  });

  const form = document.getElementById('expertApplicationForm');
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Добавьте проверку CSRF токена
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
                'X-CSRFToken': csrfToken // Добавляем в заголовки
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
        alert('Ваша заявка успешно отправлена! Мы рассмотрим её в ближайшее время.');
        form.reset();
        window.location.href = data.redirect;
      } else {
        alert(data.message || 'Произошла ошибка');
      }

    } catch (error) {
      alert(error.message || 'Ошибка соединения');
    }
  });
});