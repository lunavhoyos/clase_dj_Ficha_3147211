(function() {
    'use strict';
    
    function initSPAMotor() {
        document.addEventListener('click', function(e) {
            const loadSpa = e.target.closest('.load-spa');
            if (!loadSpa) return;
            
            e.preventDefault();
            const url = loadSpa.dataset.url;
            const target = loadSpa.dataset.target;
            
            if (!url || !target) return;
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.html) {
                    document.querySelector(target).innerHTML = data.html;
                    if (data.message && data.category) {
                        showToast(data.message, data.category);
                    }
                } else if (data.html) {
                    document.querySelector(target).innerHTML = data.html;
                }
            })
            .catch(error => console.error('SPA Error:', error));
        });
        
        document.addEventListener('submit', function(e) {
            const form = e.target.closest('.ajax-form');
            if (!form) return;
            
            e.preventDefault();
            
            const formData = new FormData(form);
            const url = form.action || window.location.href;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.html) {
                    const target = form.closest('.card').parentElement;
                    target.innerHTML = data.html;
                    if (data.message) {
                        showToast(data.message, 'success');
                    }
                } else if (data.html) {
                    const modal = form.closest('.modal-body') || form.parentElement;
                    modal.innerHTML = data.html;
                }
            })
            .catch(error => console.error('Form Error:', error));
        });
        
        document.addEventListener('submit', function(e) {
            const form = e.target.closest('.ajax-delete-form');
            if (!form) return;
            
            e.preventDefault();
            
            if (!confirm('¿Está seguro de realizar esta acción?')) return;
            
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));
            
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const target = form.closest('.col');
                    if (target) target.innerHTML = '';
                    showToast(data.message, 'success');
                }
            })
            .catch(error => console.error('Delete Error:', error));
        });
    }
    
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    
    function showToast(message, category) {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            document.body.insertAdjacentHTML('beforeend', '<div class="toast-container position-fixed top-0 end-0 p-3"></div>');
        }
        
        const toastHtml = `
            <div class="toast align-items-center text-bg-${category} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        document.querySelector('.toast-container').insertAdjacentHTML('beforeend', toastHtml);
        const toastEl = document.querySelector('.toast:last-child');
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        setTimeout(() => toast.hide(), 4000);
    }
    
    document.addEventListener('DOMContentLoaded', initSPAMotor);
})();