document.addEventListener('DOMContentLoaded', function() {
  const registrationForm = document.getElementById('registrationForm');
  const phoneInput = document.getElementById('phoneInput');
  const passwordInput = document.getElementById('passwordInput');
  const confirmPasswordInput = document.getElementById('confirmPasswordInput');
  const registerBtn = document.getElementById('registerBtn');

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

  /* ========== ВАЛИДАЦИЯ ПАРОЛЯ (8-20 СИМВОЛОВ) ========== */
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

  /* ========== ПРОВЕРКА СОВПАДЕНИЯ ПАРОЛЕЙ ========== */
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

  /* ========== ПРОВЕРКА ТЕЛЕФОНА ========== */
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

  /* ========== ПРОВЕРКА ВСЕХ ПОЛЕЙ ========== */
  function validateAllFields() {
    let allValid = true;
    
    // Проверка ФИО
    const nameFields = ['lastName', 'firstName', 'middleName'];
    nameFields.forEach(id => {
      const field = document.getElementById(id);
      if (!field.value.trim()) {
        allValid = false;
        field.classList.add('error');
      } else {
        field.classList.remove('error');
      }
    });

    // Проверка email
    const email = document.getElementById('email');
    if (!email.value.trim()) {
      allValid = false;
      email.classList.add('error');
    } else {
      email.classList.remove('error');
    }

    // Проверка телефона
    if (!validatePhone()) {
      allValid = false;
      phoneInput.classList.add('error');
    } else {
      phoneInput.classList.remove('error');
    }

    // Проверка пароля
    if (!validatePassword(passwordInput.value)) {
      allValid = false;
      passwordInput.classList.add('error');
    } else {
      passwordInput.classList.remove('error');
    }

    // Проверка подтверждения пароля
    if (!checkPasswordsMatch()) {
      allValid = false;
      confirmPasswordInput.classList.add('error');
    } else {
      confirmPasswordInput.classList.remove('error');
    }

    // Проверка чекбокса
    const termsCheckbox = document.getElementById('termsCheckbox');
    if (!termsCheckbox.checked) {
      allValid = false;
      termsCheckbox.classList.add('error');
    } else {
      termsCheckbox.classList.remove('error');
    }

    return allValid;
  }

  /* ========== ОБРАБОТЧИКИ СОБЫТИЙ ========== */
  // Динамическая валидация при вводе
  passwordInput.addEventListener('input', function() {
    validatePassword(this.value);
    checkPasswordsMatch();
  });

  confirmPasswordInput.addEventListener('input', checkPasswordsMatch);
  phoneInput.addEventListener('input', validatePhone);

  // Обработка клика по кнопке регистрации
  registerBtn.addEventListener('click', function(e) {
    e.preventDefault();
    
    if (validateAllFields()) {
      // Все поля валидны - перенаправляем
      window.location.href = 'registration/confirm';
    } else {
      // Показываем общее сообщение об ошибке
      alert('Пожалуйста, заполните все обязательные поля правильно.');
    }
  });

  // Обработка отправки формы (на случай, если пользователь нажмет Enter)
  registrationForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (validateAllFields()) {
      window.location.href = 'registration/confirm';
    } else {
      alert('Пожалуйста, заполните все обязательные поля правильно.');
    }
  });
});