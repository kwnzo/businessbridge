// Обратный отсчет и перенаправление
let seconds = 5;
const countdownElement = document.querySelector('.countdown');

const timer = setInterval(() => {
  seconds--;
  countdownElement.textContent = seconds;
   
    if (seconds <= 0) {
        clearInterval(timer);
        window.location.href = '/index';
    }
}, 1000);

// Отмена перенаправления если пользователь кликнул кнопку
document.querySelector('.btn').addEventListener('click', () => {
    clearInterval(timer);
});