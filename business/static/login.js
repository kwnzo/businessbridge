document.addEventListener('DOMContentLoaded', function() {
    const phoneBtn = document.getElementById('phoneBtn');
    const emailBtn = document.getElementById('emailBtn');
    const phoneInput = document.getElementById('phoneInput');
    const inputIcon = document.querySelectorAll('#inputIcon')[0];
    
    let isPhoneMode = true; // флаг: сейчас телефон или почта
    
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
  
      // Сохраним функцию маски, чтобы потом убрать
      input._maskInputHandler = maskInput;
    }
  
    function removePhoneMask(input) {
      if (input._maskInputHandler) {
        input.removeEventListener('input', input._maskInputHandler);
        delete input._maskInputHandler;
      }
      input.removeEventListener('focus', () => {});
      input.removeEventListener('blur', () => {});
    }
  
    applyPhoneMask(phoneInput); // изначально маска на телефоне
  
    /* ========== ПЕРЕКЛЮЧЕНИЕ ТЕЛЕФОН ↔ ПОЧТА ========== */
    phoneBtn.addEventListener('click', function() {
      if (isPhoneMode) return; // уже в режиме телефона
  
      isPhoneMode = true;
      phoneBtn.classList.add('active');
      emailBtn.classList.remove('active');
  
      phoneInput.type = 'tel';
      phoneInput.placeholder = 'Номер телефона';
      phoneInput.value = '';
  
      inputIcon.src = "static/phone.png";
  
      applyPhoneMask(phoneInput); // снова применяем маску
    });
  
    emailBtn.addEventListener('click', function() {
      if (!isPhoneMode) return; // уже в режиме почты
  
      isPhoneMode = false;
      emailBtn.classList.add('active');
      phoneBtn.classList.remove('active');
  
      removePhoneMask(phoneInput); // убираем маску
      phoneInput.type = 'email';
      phoneInput.placeholder = 'Электронная почта';
      phoneInput.value = '';
  
      inputIcon.src = "static/mail.png";
    });
  });
  