document.addEventListener('DOMContentLoaded', function () {
    const avatarUpload = document.getElementById('avatarUpload');
    const avatarPreview = document.getElementById('avatarPreview');
    const removeAvatarBtn = document.getElementById('removeAvatarBtn');
    const removeAvatarInput = document.getElementById('removeAvatar');
  
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    const confirmDeleteYes = document.getElementById('confirmDeleteYes');
    const confirmDeleteNo = document.getElementById('confirmDeleteNo');
  
    const phoneInput = document.getElementById('phone');
    const form = document.getElementById('editProfileForm');
  
    const resultModal = document.getElementById('resultModal');
    const modalMessage = document.getElementById('modal-message');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
  
    if (avatarUpload) {
        avatarUpload.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    avatarPreview.src = event.target.result;
                    if (removeAvatarInput) {
                        removeAvatarInput.value = 'false';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
  
    if (removeAvatarBtn && removeAvatarInput && confirmDeleteModal) {
        removeAvatarBtn.addEventListener('click', function () {
            confirmDeleteModal.classList.add('show');
        });
  
        confirmDeleteYes.addEventListener('click', function () {
            avatarPreview.src = removeAvatarBtn.dataset.defaultAvatar;
            removeAvatarInput.value = 'true';
            confirmDeleteModal.classList.remove('show');
        });
  
        confirmDeleteNo.addEventListener('click', function () {
            confirmDeleteModal.classList.remove('show');
        });
  
        confirmDeleteModal.addEventListener('click', function (e) {
            if (e.target === confirmDeleteModal) {
                confirmDeleteModal.classList.remove('show');
            }
        });
    }
  
    if (phoneInput) {
        phoneInput.addEventListener('input', function (e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 1) {
                value = value.substring(1);
            }
            let formattedValue = '+7 (';
            if (value.length > 0) formattedValue += value.substring(0, 3);
            if (value.length > 3) formattedValue += ') ' + value.substring(3, 6);
            if (value.length > 6) formattedValue += '-' + value.substring(6, 8);
            if (value.length > 8) formattedValue += '-' + value.substring(8, 10);
            e.target.value = formattedValue;
        });
    }
  
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(form);
  
        fetch(form.getAttribute('data-action'), {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                modalMessage.textContent = data.message;
                resultModal.classList.add('show');
                modalCloseBtn.onclick = function () {
                    if (data.success) {
                        window.location.href = data.redirect;
                    } else {
                        resultModal.classList.remove('show');
                    }
                };
            })
            .catch(error => {
                modalMessage.textContent = 'Произошла ошибка при отправке данных';
                resultModal.classList.add('show');
                modalCloseBtn.onclick = function () {
                    resultModal.classList.remove('show');
                };
            });
    });
  
    resultModal.addEventListener('click', function (e) {
        if (e.target === resultModal) {
            resultModal.classList.remove('show');
        }
    });
  });
  