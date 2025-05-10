document.addEventListener('DOMContentLoaded', function() {
  // Элементы формы
  const registrationForm = document.getElementById('registrationForm');
  const phoneInput = document.getElementById('phoneInput');
  const passwordInput = document.getElementById('passwordInput');
  const confirmPasswordInput = document.getElementById('confirmPasswordInput');
  const termsCheckbox = document.getElementById('termsCheckbox');

  // Модальное окно
  const modal = document.createElement('div');
  modal.className = 'custom-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-body">
        <p id="modal-message"></p>
      </div>
      <div class="modal-footer">
        <button class="modal-close-btn">OK</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  /* ========== МОДАЛЬНЫЕ ОКНА ========== */
  function showModal(message) {
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = message;
    modal.style.display = 'flex';
  }

  function closeModal() {
    modal.style.display = 'none';
  }

  /* ========== МАСКА ТЕЛЕФОНА ========== */
  function applyPhoneMask(input) {
    input.addEventListener('input', function(e) {
      let value = e.target.value.replace(/\D/g, '');
      
      if (value.length > 0 && value[0] !== '7') {
        value = '7' + value;
      }
      
      value = value.substring(0, 11);
      let formattedValue = '+7 (';
      
      if (value.length > 1) formattedValue += value.substring(1, 4);
      if (value.length > 4) formattedValue += ') ' + value.substring(4, 7);
      if (value.length > 7) formattedValue += '-' + value.substring(7, 9);
      if (value.length > 9) formattedValue += '-' + value.substring(9, 11);
      
      e.target.value = formattedValue;
    });
  }

  applyPhoneMask(phoneInput);

  /* ========== ВАЛИДАЦИЯ ПОЛЕЙ ========== */
  function validatePassword() {
    const errorElement = document.getElementById('passwordError');
    const password = passwordInput.value;
    
    if (password.length < 8 || password.length > 20) {
      errorElement.textContent = password.length < 8 
        ? 'Минимум 8 символов' 
        : 'Максимум 20 символов';
      return false;
    }
    errorElement.textContent = '';
    return true;
  }

  function checkPasswordsMatch() {
    const errorElement = document.getElementById('confirmPasswordError');
    if (passwordInput.value !== confirmPasswordInput.value) {
      errorElement.textContent = 'Пароли не совпадают';
      return false;
    }
    errorElement.textContent = '';
    return true;
  }

  function validatePhone() {
    const errorElement = document.getElementById('phoneError');
    const phoneValue = phoneInput.value.replace(/\D/g, '');
    
    if (phoneValue.length < 11) {
      errorElement.textContent = 'Введите полный номер';
      return false;
    }
    errorElement.textContent = '';
    return true;
  }

  /* ========== ОБРАБОТЧИК ОТПРАВКИ ========== */
  registrationForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Валидация данных
    if (!validatePassword() || !checkPasswordsMatch() || !validatePhone() || !termsCheckbox.checked) {
        showModal('Заполните все поля правильно!');
        return;
    }

    // Сбор данных
    const formData = {
        firstNames: document.getElementById('firstName').value,
        lastNames: document.getElementById('lastName').value,
        middleNames: document.getElementById('middleName').value,
        phoneInputs: phoneInput.value.replace(/\D/g, ''),  // Очистка номера
        emails: document.getElementById('email').value,
        passwordInputs: passwordInput.value,
        csrf_token: document.querySelector('[name="csrf_token"]').value
    };

    try {
        const response = await fetch('/reg', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': formData.csrf_token
            },
            body: new URLSearchParams(formData)
        });

        // Обработка не-JSON ответов
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Сервер вернул неверный формат данных');
        }

        const data = await response.json();

        if (data.success) {
            window.location.href = data.redirect;
        } else {
            showModal(data.message || 'Ошибка регистрации');
        }
    } catch (error) {
        showModal(error.message);
        console.error('Ошибка:', error);
    }
  });

  /* ========== ДИНАМИЧЕСКАЯ ВАЛИДАЦИЯ ========== */
  passwordInput.addEventListener('input', validatePassword);
  confirmPasswordInput.addEventListener('input', checkPasswordsMatch);
  phoneInput.addEventListener('input', validatePhone);
  
  // Закрытие модального окна
  document.querySelector('.modal-close-btn').addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => e.target === modal && closeModal());
});