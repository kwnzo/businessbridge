document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phoneInput');
    const passwordInput = document.getElementById('passwordInput');
    const confirmPasswordInput = document.getElementById('confirmPasswordInput');
    
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
     
    // Применяем маску к полю телефона
    applyPhoneMask(phoneInput);
     
    /* ========== ПРОВЕРКА ПАРОЛЕЙ ========== */
    function checkPasswords() {
      const password = passwordInput.value;
      const confirmPassword = confirmPasswordInput.value;
      
      if (password && confirmPassword && password !== confirmPassword) {
        confirmPasswordInput.setCustomValidity('Пароли не совпадают');
        confirmPasswordInput.classList.add('error');
        return false;
      } else {
        confirmPasswordInput.setCustomValidity('');
        confirmPasswordInput.classList.remove('error');
        document.getElementById('confirmPasswordError').textContent = '';
        return true;
      }
    }
      
    // Слушатели событий для проверки паролей
    [passwordInput, confirmPasswordInput].forEach(input => {
      input.addEventListener('input', checkPasswords);
    });
     
    // Валидация формы при отправке
    document.querySelector('.auth-form').addEventListener('submit', function(e) {
      if (!checkPasswords()) {
        e.preventDefault();
      }
        
      // Дополнительная валидация телефона
      const phoneValue = phoneInput.value.replace(/\D/g, '');
      if (phoneValue.length < 11) {
        phoneInput.classList.add('error');
        document.getElementById('phoneError').textContent = 'Введите полный номер телефона';
        e.preventDefault();
      } else {
        phoneInput.classList.remove('error');
        document.getElementById('phoneError').textContent = '';
      }
    });
  });