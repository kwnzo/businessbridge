document.addEventListener('DOMContentLoaded', function() {
  const phoneBtn = document.getElementById('phoneBtn');
  const emailBtn = document.getElementById('emailBtn');
  let phoneInput = document.getElementById('phoneInput'); // Используем let вместо const
  const passwordInput = document.getElementById('passwordInput');
  const inputIcon = document.querySelectorAll('#inputIcon')[0];
  const loginForm = document.getElementById('loginForm');
  
  let isPhoneMode = true; // флаг: сейчас телефон или почта
  
  /* ========== МАСКА ТЕЛЕФОНА ========== */
  function createPhoneMask() {
    // Удаляем все предыдущие обработчики
    phoneInput.replaceWith(phoneInput.cloneNode(true));
    const newInput = document.getElementById('phoneInput');
    
    newInput.addEventListener('input', function(e) {
      let value = e.target.value.replace(/\D/g, '');

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

      e.target.value = formattedValue;
    });

    newInput.addEventListener('focus', function() {
      if (this.value === '') {
        this.value = '+7 (';
      }
    });

    newInput.addEventListener('blur', function() {
      if (this.value === '+7 (') {
        this.value = '';
      }
    });
    
    return newInput;
  }

  function removePhoneMask() {
    // Просто заменяем input на новый чистый элемент
    phoneInput.replaceWith(phoneInput.cloneNode(true));
    return document.getElementById('phoneInput');
  }

  // Инициализация маски при загрузке
  phoneInput = createPhoneMask();
  
  /* ========== ВАЛИДАЦИЯ ПОЛЕЙ ========== */
  function validatePhone(phone) {
    const digits = phone.replace(/\D/g, '');
    return digits.length === 11;
  }
  
  function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }
  
  function validatePassword(password) {
    return password.length >= 8 && password.length <= 20;
  }
  
  function validateForm() {
    let isValid = true;
    
    if (isPhoneMode) {
      if (!validatePhone(phoneInput.value)) {
        phoneInput.classList.add('error');
        isValid = false;
      } else {
        phoneInput.classList.remove('error');
      }
    } else {
      if (!validateEmail(phoneInput.value)) {
        phoneInput.classList.add('error');
        isValid = false;
      } else {
        phoneInput.classList.remove('error');
      }
    }
    
    if (!validatePassword(passwordInput.value)) {
      passwordInput.classList.add('error');
      isValid = false;
    } else {
      passwordInput.classList.remove('error');
    }
    
    return isValid;
  }

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

  function showModal(message) {
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = message;
    modal.style.display = 'flex';
  }
  function closeModal() {
    modal.style.display = 'none';
  }

  /* ========== ОБРАБОТКА ОТПРАВКИ ФОРМЫ ========== */
  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!validateForm()) return;
  
    // Сбор данных формы
    const formData = new FormData();
    const loginValue = isPhoneMode 
      ? phoneInput.value.replace(/\D/g, '')  // Чистим номер от форматирования
      : phoneInput.value;
    
    formData.append('login', loginValue);
    formData.append('password', passwordInput.value);
    formData.append('csrf_token', document.querySelector('[name="csrf_token"]').value);
  
    try {
      // Отправка POST-запроса
      const response = await fetch('/login', {
        method: 'POST',
        body: formData
      });
  
      const data = await response.json();
      
      if (data.success) {
        window.location.href = data.redirect; // Перенаправление от сервера
      } else {
        showModal(data.message || 'Ошибка авторизации');
      }
      
    } catch (error) {
      alert('Ошибка соединения с сервером');
    }
  });
  
  phoneInput.addEventListener('input', function() {
    if (isPhoneMode ? validatePhone(phoneInput.value) : validateEmail(phoneInput.value)) {
      phoneInput.classList.remove('error');
    }
  });
  
  passwordInput.addEventListener('input', function() {
    if (validatePassword(passwordInput.value)) {
      passwordInput.classList.remove('error');
    }
  });

  /* ========== ПЕРЕКЛЮЧЕНИЕ ТЕЛЕФОН ↔ ПОЧТА ========== */
  phoneBtn.addEventListener('click', function() {
    if (isPhoneMode) return;

    isPhoneMode = true;
    phoneBtn.classList.add('active');
    emailBtn.classList.remove('active');

    // Удаляем текущий input и создаем новый с маской
    phoneInput = removePhoneMask();
    phoneInput = createPhoneMask();
    
    phoneInput.type = 'tel';
    phoneInput.placeholder = 'Номер телефона';
    phoneInput.value = '';
    phoneInput.classList.remove('error');

    inputIcon.src = "static/img/phone.png";
  });

  emailBtn.addEventListener('click', function() {
    if (!isPhoneMode) return;

    isPhoneMode = false;
    emailBtn.classList.add('active');
    phoneBtn.classList.remove('active');

    // Удаляем маску полностью
    phoneInput = removePhoneMask();
    
    phoneInput.type = 'email';
    phoneInput.placeholder = 'Электронная почта';
    phoneInput.value = '';
    phoneInput.classList.remove('error');

    inputIcon.src = "static/img/mail.png";
    
    // Добавляем обработчик input для валидации email
    phoneInput.addEventListener('input', function() {
      if (validateEmail(phoneInput.value)) {
        phoneInput.classList.remove('error');
      }
    });
  });
  document.querySelector('.modal-close-btn').addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => e.target === modal && closeModal());
});