// Модальное окно для отображения сообщений
function showModal(message, isSuccess = false) {
  const modal = document.getElementById('resultModal');
  const modalMessage = document.getElementById('modal-message');
  
  modalMessage.textContent = message;
  
  // Можно добавить класс для стилизации успешных/ошибочных сообщений
  if (isSuccess) {
    modalMessage.classList.add('success-message');
    modalMessage.classList.remove('error-message');
  } else {
    modalMessage.classList.add('error-message');
    modalMessage.classList.remove('success-message');
  }
  
  modal.style.display = 'flex';
}

// Закрытие модального окна
document.getElementById('modalCloseBtn').addEventListener('click', function() {
  document.getElementById('resultModal').style.display = 'none';
});

// Закрытие при клике вне модального окна
window.addEventListener('click', function(event) {
  const modal = document.getElementById('resultModal');
  if (event.target === modal) {
    modal.style.display = 'none';
  }
});

// Отображение имени выбранного файла
document.getElementById('image').addEventListener('change', function(e) {
  const fileName = e.target.files[0]?.name || 'Файл не выбран';
  document.getElementById('file-name').textContent = fileName;
});

// Обработка отправки формы
document.getElementById('article-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const title = document.getElementById('title').value.trim();
  const content = document.getElementById('content').value.trim();
  const category = document.getElementById('category').value;
  const imageFile = document.getElementById('image').files[0];
  
  // Валидация полей
  if (!title) {
    showModal('Пожалуйста, введите заголовок статьи');
    return;
  }
  
  if (!content) {
    showModal('Пожалуйста, напишите текст статьи');
    return;
  }
  
  if (!category) {
    showModal('Пожалуйста, выберите категорию статьи');
    return;
  }
  
  if (!imageFile) {
    showModal('Пожалуйста, добавьте изображение');
    return;
  }
  
  const formData = new FormData();
  formData.append('title', title);
  formData.append('content', content);
  formData.append('category', category);
  formData.append('image', imageFile);
  formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
  
  // Логирование данных перед отправкой (для отладки)
  console.log('Отправляемые данные:');
  for (let [key, value] of formData.entries()) {
    console.log(key, value);
  }
  
  try {
    const response = await fetch('/profile/create-publication', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      showModal('Статья успешно опубликована!', true);
      // Перенаправление после закрытия модального окна
      document.getElementById('modalCloseBtn').addEventListener('click', function() {
        window.location.href = '/profile';
      }, { once: true });
    } else {
      showModal('Ошибка: ' + (result.message || 'Ошибка при публикации статьи'));
    }
  } catch (error) {
    console.error('Ошибка:', error);
    showModal('Произошла ошибка при отправке данных');
  }
});