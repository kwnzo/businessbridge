// Функция для показа деталей заявки
function showRequestDetails(requestId) {
  fetch(`/admin/requests/expert/${requestId}/details`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        document.getElementById('requestDetailsContent').innerHTML = `
          <p><strong>Компания:</strong> ${data.request.company}</p>
          <p><strong>Должность:</strong> ${data.request.position}</p>
          <p><strong>Экспертиза:</strong> ${data.request.expertise}</p>
          ${data.request.other_expertise ? `<p><strong>Другая экспертиза:</strong> ${data.request.other_expertise}</p>` : ''}
          <p><strong>Опыт работы:</strong> ${data.request.experience} лет</p>
          <p><strong>Описание:</strong></p>
          <p>${data.request.description}</p>
        `;
        document.getElementById('requestDetailsModal').style.display = 'block';
      }
    });
}

// Функция для одобрения заявки
function approveRequest(requestId) {
  if (confirm('Вы уверены, что хотите одобрить эту заявку? Пользователь получит права эксперта.')) {
    fetch(`/admin/requests/expert/${requestId}/approve`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
        'Content-Type': 'application/json'
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        location.reload();
      } else {
        alert('Ошибка: ' + data.message);
      }
    });
  }
}

// Функция для открытия модального окна отказа
function rejectRequest(requestId) {
  showRejectModal(requestId);
}

// Закрытие модальных окон
document.querySelectorAll('.admin-expert-close').forEach(btn => {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.admin-expert-modal').forEach(modal => {
      modal.style.display = 'none';
    });
  });
});

// Закрытие по клику вне модального окна
window.addEventListener('click', function(event) {
  document.querySelectorAll('.admin-expert-modal').forEach(modal => {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
});

let currentRequestId = null;

// Показать модальное окно отказа
function showRejectModal(requestId) {
  currentRequestId = requestId;
  document.getElementById('rejectionReason').value = '';
  document.getElementById('rejectModal').style.display = 'block';
}

// Закрыть модальное окно отказа
function closeRejectModal() {
  document.getElementById('rejectModal').style.display = 'none';
}

// Подтверждение отказа
function confirmReject() {
  const reason = document.getElementById('rejectionReason').value.trim();
  if (!reason) {
    alert('Пожалуйста, укажите причину отказа');
    return;
  }

  fetch(`/admin/requests/expert/${currentRequestId}/reject`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ reason: reason })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      alert('Ошибка: ' + data.message);
    }
  });
}

// Назначение обработчиков событий после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
  // Добавляем CSRF-токен в meta-тег, если его нет
  if (!document.querySelector('meta[name="csrf-token"]')) {
    const meta = document.createElement('meta');
    meta.name = 'csrf-token';
    meta.content = '{{ csrf_token_value }}';
    document.head.appendChild(meta);
  }
});