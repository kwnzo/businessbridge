document.addEventListener('DOMContentLoaded', function() {
  const phoneBtn = document.getElementById('phoneBtn');
  const emailBtn = document.getElementById('emailBtn');
  const inputIcon = document.querySelector('.input-group .icon');
  const phoneInput = document.getElementById('phoneInput');
  const passwordInput = document.getElementById('passwordInput');
  const authForm = document.querySelector('.auth-form');
  
  // Текущий режим ввода (по умолчанию телефон)
  let currentMode = 'phone';
  
  /* ========== МАСКА ТЕЛЕФОНА ========== */
  function applyPhoneMask(input) {
      function maskInput(event) {
          let value = event.target.value.replace(/\D/g, '');
          
          // Если поле не пустое и не начинается с 7, добавляем 7
          if (value.length > 0 && value[0] !== '7') {
              value = '7' + value;
          }
           
          // Ограничиваем длину до 11 цифр (7 + 10 цифр номера)
          value = value.substring(0, 11);
          
          // Форматируем по маске только если есть введенные цифры
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
  
  // Применяем маску к полю телефона при загрузке
  applyPhoneMask(phoneInput);
  
  /* ========== ПЕРЕКЛЮЧЕНИЕ МЕЖДУ ТЕЛЕФОНОМ И ПОЧТОЙ ========== */
  function switchToPhone() {
      currentMode = 'phone';
      phoneBtn.classList.add('active');
      emailBtn.classList.remove('active');
      inputIcon.src = "static/phone.png";
      phoneInput.type = 'tel';
      phoneInput.placeholder = 'Номер телефона';
      phoneInput.value = '';
      
      // Восстанавливаем обработчик маски
      phoneInput.removeEventListener('input', emailInputHandler);
      applyPhoneMask(phoneInput);
  }
  
  function switchToEmail() {
      currentMode = 'email';
      emailBtn.classList.add('active');
      phoneBtn.classList.remove('active');
      inputIcon.src = "static/mail.png";
      phoneInput.type = 'email';
      phoneInput.placeholder = 'Электронная почта';
      phoneInput.value = '';
      
      // Удаляем обработчик маски телефона
      phoneInput.replaceWith(phoneInput.cloneNode(true));
      phoneInput = document.getElementById('phoneInput');
      
      // Добавляем обработчик для email (если нужно)
      phoneInput.addEventListener('input', emailInputHandler);
  }
  
  // Обработчик ввода для email (можно добавить валидацию)
  function emailInputHandler(e) {
      // Можно добавить валидацию email при необходимости
  }
  
  // Обработчики кнопок переключения
  phoneBtn.addEventListener('click', function(e) {
      e.preventDefault();
      if (currentMode !== 'phone') {
          switchToPhone();
      }
  });
  
  emailBtn.addEventListener('click', function(e) {
      e.preventDefault();
      if (currentMode !== 'email') {
          switchToEmail();
      }
  });
  
  /* ========== ВАЛИДАЦИЯ ФОРМЫ ========== */
  authForm.addEventListener('submit', function(e) {
      let isValid = true;
      
      // Проверка телефона/почты
      if (currentMode === 'phone') {
          const phoneValue = phoneInput.value.replace(/\D/g, '');
          if (phoneValue.length < 11) {
              phoneInput.classList.add('error');
              isValid = false;
          } else {
              phoneInput.classList.remove('error');
          }
      } else {
          // Простая проверка email (можно улучшить)
          const emailValue = phoneInput.value;
          if (!emailValue.includes('@') || !emailValue.includes('.')) {
              phoneInput.classList.add('error');
              isValid = false;
          } else {
              phoneInput.classList.remove('error');
          }
      }
      
      // Проверка пароля
      if (passwordInput.value.length < 6) {
          passwordInput.classList.add('error');
          isValid = false;
      } else {
          passwordInput.classList.remove('error');
      }
      
      if (!isValid) {
          e.preventDefault();
      }
  });
});