document.addEventListener('DOMContentLoaded', function() {
  // Создаем модальное окно
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

  // Элементы формы
  const registrationForm = document.getElementById('registrationForm');
  const phoneInput = document.getElementById('phoneInput');
  const passwordInput = document.getElementById('passwordInput');
  const confirmPasswordInput = document.getElementById('confirmPasswordInput');
  const termsCheckbox = document.getElementById('termsCheckbox');
  const registerBtn = document.getElementById('registerBtn');
  const modalCloseBtn = document.querySelector('.modal-close-btn');

  /* ========== МОДАЛЬНЫЕ ОКНА ========== */
  function showModal(message) {
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = message;
    modal.style.display = 'flex'; // Используем flex для центрирования
    
    // Центрируем текст сообщения
    modalMessage.style.textAlign = 'center';
  }

  // Закрытие модального окна
  function closeModal() {
    modal.style.display = 'none';
  }

  modalCloseBtn.addEventListener('click', closeModal);
  
  // Закрытие при клике вне модального окна
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeModal();
    }
  });


  /* ========== МАСКА ТЕЛЕФОНА ========== */
  function applyPhoneMask(input) {
    function maskInput(event) {
      let value = event.target.value.replace(/\D/g, '');
      
      if (value.length > 0 && value[0] !== '7') {
        value = '7' + value;
      }
       
      value = value.substring(0, 11);
      
      let formattedValue = '';
      if (value.length > 0) {
        formattedValue = '+7 (';
        if (value.length > 1) {
          formattedValue += value.substring(1, 4);
        }
        if (value.length > 4) {
          formattedValue += ') ' + value.substring(4, 7);
        }
        if (value.length > 7) {
          formattedValue += '-' + value.substring(7, 9);
        }
        if (value.length > 9) {
          formattedValue += '-' + value.substring(9, 11);
        }
      }
       
      event.target.value = formattedValue;
    }
      
    input.addEventListener('input', maskInput);
    input.addEventListener('focus', function() {
      if (input.value === '') {
        input.value = '+7 (';
      }
    });
    input.addEventListener('blur', function() {
      if (input.value === '+7 (') {
        input.value = '';
      }
    });
  }

  applyPhoneMask(phoneInput);

  /* ========== ВАЛИДАЦИЯ ПОЛЕЙ ========== */
  function validatePassword(password) {
    const errorElement = document.getElementById('passwordError');
    
    if (password.length < 8) {
      errorElement.textContent = 'Минимум 8 символов';
      return false;
    } else if (password.length > 20) {
      errorElement.textContent = 'Максимум 20 символов';
      return false;
    } else {
      errorElement.textContent = '';
      return true;
    }
  }

  function checkPasswordsMatch() {
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    const errorElement = document.getElementById('confirmPasswordError');
    
    if (password && confirmPassword && password !== confirmPassword) {
      errorElement.textContent = 'Пароли не совпадают';
      return false;
    } else {
      errorElement.textContent = '';
      return true;
    }
  }

  function validatePhone() {
    const phoneValue = phoneInput.value.replace(/\D/g, '');
    const errorElement = document.getElementById('phoneError');
    
    if (phoneValue.length < 11) {
      errorElement.textContent = 'Введите полный номер телефона';
      return false;
    } else {
      errorElement.textContent = '';
      return true;
    }
  }

  function validateAllFields() {
    // Проверка ФИО
    const nameFields = ['lastName', 'firstName', 'middleName'];
    for (const id of nameFields) {
      const field = document.getElementById(id);
      if (!field.value.trim()) {
        showModal('Пожалуйста, заполните все обязательные поля правильно');
        field.classList.add('error');
        return false;
      }
    }

    // Проверка email
    const email = document.getElementById('email');
    if (!email.value.trim()) {
      showModal('Пожалуйста, заполните все обязательные поля правильно');
      email.classList.add('error');
      return false;
    }

    // Проверка телефона
    if (!validatePhone()) {
      showModal('Пожалуйста, заполните все обязательные поля правильно');
      phoneInput.classList.add('error');
      return false;
    }

    // Проверка пароля
    if (!validatePassword(passwordInput.value)) {
      showModal('Пожалуйста, заполните все обязательные поля правильно');
      passwordInput.classList.add('error');
      return false;
    }

    // Проверка подтверждения пароля
    if (!checkPasswordsMatch()) {
      showModal('Пожалуйста, заполните все обязательные поля правильно');
      confirmPasswordInput.classList.add('error');
      return false;
    }

    // Проверка чекбокса
    if (!termsCheckbox.checked) {
      showModal('Необходимо принять условия использования');
      termsCheckbox.classList.add('error');
      return false;
    }

    return true;
  }

  /* ========== ОБРАБОТЧИКИ СОБЫТИЙ ========== */
  // Динамическая валидация при вводе
  passwordInput.addEventListener('input', function() {
    validatePassword(this.value);
    checkPasswordsMatch();
  });

  confirmPasswordInput.addEventListener('input', checkPasswordsMatch);
  phoneInput.addEventListener('input', validatePhone);

  // Очистка ошибок при фокусе
  const allInputs = registrationForm.querySelectorAll('input');
  allInputs.forEach(input => {
    input.addEventListener('focus', function() {
      this.classList.remove('error');
      const errorElement = this.nextElementSibling;
      if (errorElement && errorElement.classList.contains('error-message')) {
        errorElement.textContent = '';
      }
    });
  });

  // Обработка отправки формы
  registrationForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (validateAllFields()) {
      window.location.href = 'reg/confirm';
    }
  });

  // Обработка клика по кнопке
  registerBtn.addEventListener('click', function(e) {
    e.preventDefault();
    
    if (validateAllFields()) {
      window.location.href = 'reg/confirm';
    }
  });
});