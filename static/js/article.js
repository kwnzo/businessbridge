document.addEventListener('DOMContentLoaded', function() {
  // Обработка лайков
  const likeButton = document.querySelector('.like-button');
  if (likeButton) {
    likeButton.addEventListener('click', async function() {
      const articleId = this.dataset.articleId;
      
      try {
        const response = await fetch('/like-article', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
          },
          body: JSON.stringify({ article_id: articleId })
        });
        
        const result = await response.json();
        
        if (result.success) {
          const likeCount = this.querySelector('span');
          likeCount.textContent = result.new_likes;
          this.classList.toggle('liked', result.liked);
        }
      } catch (error) {
        console.error('Error:', error);
      }
    });
  }
  
});