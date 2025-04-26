const phoneBtn = document.getElementById('phoneBtn');
    const emailBtn = document.getElementById('emailBtn');
    const authInput = document.getElementById('authInput');
    const inputIcon = document.getElementById('inputIcon');
  
    let maskHandler = null;
  
    // Маска телефона с автоматической подстановкой 7 при вводе
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
      maskHandler = maskInput;
      
      // Очищаем поле при переключении на телефон
      input.value = '';
    }
  
    function removePhoneMask(input) {
      if (maskHandler) {
        input.removeEventListener('input', maskHandler);
        maskHandler = null;
      }
      input.value = '';
    }
  
    // Телефон по умолчанию
    phoneBtn.addEventListener('click', () => {
      phoneBtn.classList.add('active');
      emailBtn.classList.remove('active');
  
      authInput.type = 'tel';
      authInput.placeholder = 'Номер телефона';
      inputIcon.src = 'img/phone.png';
  
      applyPhoneMask(authInput);
    });
  
    // Почта
    emailBtn.addEventListener('click', () => {
      emailBtn.classList.add('active');
      phoneBtn.classList.remove('active');
  
      removePhoneMask(authInput);
      authInput.type = 'email';
      authInput.placeholder = 'Введите почту';
      inputIcon.src = 'img/mail.png';
    });
  
    // Инициализация - поле пустое
    authInput.value = '';
    // Но применяем маску для телефона по умолчанию
    applyPhoneMask(authInput);