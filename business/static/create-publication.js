    // Отображение имени выбранного файла
    document.getElementById('image').addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name || 'Файл не выбран';
        document.getElementById('file-name').textContent = fileName;
      });
  
      async function submitArticle() {
        const title = document.getElementById('title').value.trim();
        const content = document.getElementById('content').value.trim();
        const imageFile = document.getElementById('image').files[0];
  
        // Валидация
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
          const response = await fetch('/api/articles', {
            method: 'POST',
            body: formData
          });
  
          if (response.ok) {
            alert('Статья успешно опубликована!');
            window.location.href = '/profile';
          } else {
            const errorData = await response.json();
            alert(errorData.message || 'Ошибка при публикации статьи');
          }
        } catch (error) {
          console.error('Ошибка:', error);
          alert('Произошла ошибка при отправке данных');
        }
      }