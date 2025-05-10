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
  const imageFile = document.getElementById('image').files[0];
  
  // Валидация полей
  if (!title) {
    alert('Пожалуйста, введите заголовок статьи');
    return;
  }
  
  if (!content) {
    alert('Пожалуйста, напишите текст статьи');
    return;
  }
  
  if (!imageFile) {
    alert('Пожалуйста, добавьте изображение');
    return;
  }
  
  const formData = new FormData();
  formData.append('title', title);
  formData.append('content', content);
  formData.append('image', imageFile);
  
  try {
    const response = await fetch('/profile/create-publication', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      alert('Статья успешно опубликована!');
      window.location.href = result.redirect || '/profile';
    } else {
      alert('Ошибка: ' + (result.message || 'Ошибка при публикации статьи'));
    }
  } catch (error) {
    console.error('Ошибка:', error);
    alert('Произошла ошибка при отправке данных');
  }
});