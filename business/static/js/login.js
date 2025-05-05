document.addEventListener('DOMContentLoaded', function() {
  // Элементы формы
  const phoneBtn = document.getElementById('phoneBtn');
  const emailBtn = document.getElementById('emailBtn');
  let phoneInput = document.getElementById('phoneInput');
  const passwordInput = document.getElementById('passwordInput');
  const inputIcon = document.querySelector('#inputIcon');
  const loginForm = document.getElementById('loginForm');
  let isPhoneMode = true;

  // Добавляем модальное окно
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

  // Функции для работы с модальным окном
  function showModal(message) {
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = message;
    modal.style.display = 'flex';
  }

  function closeModal() {
    modal.style.display = 'none';
  }

  /* ========== МАСКА ТЕЛЕФОНА ========== */
  function createPhoneMask() {
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
        if (value.length > 1) formattedValue += value.substring(1, 4);
        if (value.length > 4) formattedValue += ') ' + value.substring(4, 7);
        if (value.length > 7) formattedValue += '-' + value.substring(7, 9);
        if (value.length > 9) formattedValue += '-' + value.substring(9, 11);
      }

      e.target.value = formattedValue;
    });

    newInput.addEventListener('focus', function() {
      if (this.value === '') this.value = '+7 (';
    });

    newInput.addEventListener('blur', function() {
      if (this.value === '+7 (') this.value = '';
    });
    
    return newInput;
  }

  function removePhoneMask() {
    const newInput = phoneInput.cloneNode(true);
    phoneInput.replaceWith(newInput);
    return newInput;
  }

  // Инициализация маски
  phoneInput = createPhoneMask();



  /* ========== ВАЛИДАЦИЯ ПОЛЕЙ ========== */
  function validatePhone() {
    // Получаем чистые цифры номера
    const digits = phoneInput.value.replace(/\D/g, '');
    return digits.length === 11;
  }

  function validateEmail() {
    // Проверяем email только если мы в режиме почты
    if (!isPhoneMode) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(phoneInput.value.trim());
    }
    return true; // В режиме телефона всегда возвращаем true для email валидации
  }

  function validatePassword() {
    return passwordInput.value.length >= 8 && passwordInput.value.length <= 20;
  }

  function validateForm() {
    let isValid = true;
    
    if (isPhoneMode) {
      if (!validatePhone()) {
        phoneInput.classList.add('error');
        isValid = false;
      }
    } else {
      if (!validateEmail()) {
        phoneInput.classList.add('error');
        isValid = false;
      }
    }
    
    if (!validatePassword()) {
      passwordInput.classList.add('error');
      isValid = false;
    }
    
    return isValid;
}


  /* ========== ОБРАБОТКА ОТПРАВКИ ФОРМЫ ========== */
  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!validateForm()) {
      showModal('Проверьте правильность введенных данных');
      return;
    }
  
    // Получаем элементы формы
    const usersnumber = document.getElementById('phoneInput');
    const userspassword = document.getElementById('passwordInput');
    const csrfToken = document.querySelector('[name="csrf_token"]');
    
    // Проверяем, что элементы существуют
    if (!usersnumber || !userspassword || !csrfToken) {
      showModal('Ошибка формы. Пожалуйста, обновите страницу.');
      return;
    }
  
    // Создаем formData ТОЛЬКО после проверки всех элементов
    const formData = new URLSearchParams();
    formData.append('csrf_token', document.querySelector('[name="csrf_token"]').value);
    formData.append('password', passwordInput.value);
    
    if (isPhoneMode) {
        formData.append('login', phoneInput.value.replace(/\D/g, '')); // Исправлено имя параметра
    } else {
        formData.append('login', phoneInput.value.trim()); // Исправлено имя параметра
    }
  
    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': document.querySelector('[name="csrf_token"]').value  // Используем значение напрямую
        },
        body: formData
      });
  
      // Проверяем статус ответа

      if (!response.ok){
        const texterror = await response.text()
        throw new Error(`Произошла ошибка: ${response.statusText}`)
      }
  
      // Пытаемся распарсить JSON
      const data = await response.json();
  
      if (data.success) {
        window.location.href = data.redirect || '/';
      } else {
        showModal(data.message || 'Ошибка авторизации');
      }
    } catch (error) {
      console.error('Ошибка:', error);
      showModal(error.message || 'Произошла ошибка при авторизации');
    }
  });
  

  /* ========== ДИНАМИЧЕСКАЯ ВАЛИДАЦИЯ ========== */
  phoneInput.addEventListener('input', function() {
    if (isPhoneMode ? validatePhone() : validateEmail()) {
      this.classList.remove('error');
    }
  });

  passwordInput.addEventListener('input', function() {
    if (validatePassword()) {
      this.classList.remove('error');
    }
  });

  /* ========== ПЕРЕКЛЮЧЕНИЕ РЕЖИМА ========== */
  phoneBtn.addEventListener('click', function() {
    if (isPhoneMode) return;
    
    isPhoneMode = true;
    phoneBtn.classList.add('active');
    emailBtn.classList.remove('active');
    
    phoneInput = removePhoneMask();
    phoneInput = createPhoneMask();
    phoneInput.type = 'tel'; // Явно устанавливаем тип
    phoneInput.placeholder = 'Номер телефона';
    phoneInput.value = '';
    inputIcon.src = "static/img/phone.png";
    phoneInput.classList.remove('error'); // Сбрасываем ошибку
  });

  emailBtn.addEventListener('click', function() {
    if (!isPhoneMode) return;
    
    isPhoneMode = false;
    emailBtn.classList.add('active');
    phoneBtn.classList.remove('active');
    
    phoneInput = removePhoneMask();
    phoneInput.type = 'email'; // Явно устанавливаем тип
    phoneInput.placeholder = 'Электронная почта';
    phoneInput.value = '';
    inputIcon.src = "static/img/mail.png";
    phoneInput.classList.remove('error'); // Сбрасываем ошибку
  });

  /* ========== ЗАКРЫТИЕ МОДАЛЬНОГО ОКНА ========== */
  document.querySelector('.modal-close-btn').addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => e.target === modal && closeModal());
});