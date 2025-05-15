document.addEventListener('DOMContentLoaded', function() {
  // Получаем CSRF-токен из мета-тега
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

  // Обработка изменения роли
  document.querySelectorAll('.role-select').forEach(select => {
    select.addEventListener('change', function() {
      const userId = this.dataset.userId;
      const newRole = this.value;
      
      fetch(`/admin/users/${userId}/update_role`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken  // Используем полученный токен
        },
        body: JSON.stringify({ role: newRole })
      })
      .then(response => response.json())
      .then(data => {
        if (!data.success) {
          alert('Ошибка обновления роли');
          location.reload();
        }
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Ошибка обновления роли');
      });
    });
  });

  // Обработка удаления пользователя
  document.querySelectorAll('.delete-user').forEach(button => {
    button.addEventListener('click', function() {
      if (!confirm('Вы уверены, что хотите удалить этого пользователя?')) {
        return;
      }
      
      const userId = this.dataset.userId;
      
      fetch(`/admin/users/${userId}/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken  // Используем полученный токен
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          this.closest('tr').remove();
        } else {
          alert('Ошибка удаления пользователя');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Ошибка удаления пользователя');
      });
    });
  });

  // Поиск пользователей (остается без изменений)
  document.getElementById('user-search').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    document.querySelectorAll('tbody tr').forEach(row => {
      const name = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
      const email = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
      
      if (name.includes(searchTerm) || email.includes(searchTerm)) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  });
});