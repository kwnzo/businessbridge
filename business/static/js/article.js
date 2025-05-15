document.addEventListener('DOMContentLoaded', function() {
    const likeButtons = document.querySelectorAll('.like-button:not(a)');
    
    likeButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const articleId = this.dataset.articleId;
            
            try {
                const response = await fetch('/api/like', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        public_id: articleId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Обновляем состояние кнопки
                    this.classList.toggle('liked');
                    const likeText = this.querySelector('.like-text');
                    if (likeText) {
                        likeText.textContent = data.action === 'added' ? 'Убрать лайк' : 'Нравится';
                    }
                    
                    // Обновляем счетчик лайков
                    const likesCounter = document.querySelector('.article-stats .stat-item:nth-child(3) span');
                    if (likesCounter) {
                        likesCounter.textContent = data.likes_count;
                    }
                } else {
                    console.error('Ошибка:', data.message);
                    alert(data.message);
                }
            } catch (error) {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при обработке запроса');
            }
        });
    });
});