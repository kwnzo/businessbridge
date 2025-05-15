document.addEventListener('DOMContentLoaded', function() {
    // Удаление статьи (остается без изменений)
    document.querySelectorAll('.delete-article').forEach(button => {
        button.addEventListener('click', async function() {
            if (!confirm('Удалить статью?')) return;
            
            const articleId = this.dataset.articleId;
            const csrfToken = document.querySelector('[name=csrf_token]').value;
            
            try {
                const response = await fetch(`/admin/articles/${articleId}/delete`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                });
                
                const data = await response.json();
                if (data.success) {
                    this.closest('tr').remove();
                } else {
                    alert('Ошибка: ' + (data.message || 'Не удалось удалить статью'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Ошибка соединения');
            }
        });
    });

    // Поиск статей
    document.getElementById('article-search').addEventListener('input', function() {
        const term = this.value.toLowerCase();
        document.querySelectorAll('tbody tr').forEach(row => {
            const title = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
            const author = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
            row.style.display = (title.includes(term) || author.includes(term)) ? '' : 'none';
        });
    });
});

