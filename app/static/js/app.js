document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-confirm]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(el) { return new bootstrap.Tooltip(el); });

    document.querySelectorAll('form[method="POST"]').forEach(function(form) {
        if (form.hasAttribute('data-no-ajax')) return;
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Clear previous errors
            form.querySelectorAll('.invalid-feedback.dynamic-error').forEach(el => el.remove());
            form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;

            const formData = new FormData(form);
            const url = form.action || window.location.href;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });

                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                const data = await response.json().catch(() => null);
                
                if (!response.ok && data && data.errors) {
                    for (const [field, msgs] of Object.entries(data.errors)) {
                        const input = form.querySelector(`[name="${field}"]`);
                        if (input) {
                            input.classList.add('is-invalid');
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'invalid-feedback dynamic-error';
                            errorDiv.innerHTML = msgs.join('<br>');
                            
                            // For checkboxes/radios wrapped in divs
                            if (input.type === 'checkbox' || input.type === 'radio') {
                                input.parentElement.parentElement.appendChild(errorDiv);
                            } else {
                                input.parentElement.appendChild(errorDiv);
                            }
                            errorDiv.style.display = 'block';
                        } else if (field === '_general') {
                            alert(msgs.join('\n'));
                        }
                    }
                } else if (response.ok) {
                    if (data && data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.reload();
                    }
                } else {
                    console.error("Unexpected error", response.status);
                    alert("An unexpected error occurred. Please try again.");
                }
            } catch (err) {
                console.error("Form submission failed", err);
                alert("Failed to submit form. Please check your connection.");
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    });
});
