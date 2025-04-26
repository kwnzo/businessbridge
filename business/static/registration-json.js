document.addEventListener('DOMContentLoaded', function() {
    const registrationForm = document.getElementById('registrationForm');
    registrationForm.addEventListener('submit', function(event) {
      event.preventDefault(); // Предотвращаем стандартную отправку формы

      // Собираем данные из полей формы
      const lastName = document.getElementById('lastName').value;
      const firstName = document.getElementById('firstName').value;
      const middleName = document.getElementById('middleName').value;
      const phone = document.getElementById('phoneInput').value;
      const email = document.getElementById('email').value;
      const password = document.getElementById('passwordInput').value;
      const confirmPassword = document.getElementById('confirmPasswordInput').value;

      // Проверяем, что пароли совпадают
      if (password !== confirmPassword) {
        alert('Пароли не совпадают');
        return;
      }

      // Создаем объект для отправки данных
      const formData = {
        lastName: lastName,
        firstName: firstName,
        middleName: middleName,
        phone: phone,
        email: email,
        password: password
      };

      // Отправляем данные через AJAX
      fetch('register.php', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('Регистрация успешна!');
          window.location.href = 'login.html'; // Перенаправление на страницу входа
        } else {
          alert('Ошибка регистрации: ' + data.message);
        }
      })
      .catch(error => {
        console.error('Ошибка:', error);
      });
    });
  });