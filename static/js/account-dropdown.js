document.addEventListener('DOMContentLoaded', function() {
    // Обработчик клика по кнопке аккаунта
    const accountButton = document.querySelector('.account-button-if-login');
    if (accountButton) {
        accountButton.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdown = this.closest('.account-dropdown').querySelector('.account-dropdown-content');
            dropdown.classList.toggle('show');
        });
    }

    // Закрытие меню при клике вне его
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.account-dropdown')) {
            const dropdowns = document.querySelectorAll('.account-dropdown-content');
            dropdowns.forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
});