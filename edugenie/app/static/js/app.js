// EduGenie - Lightweight Frontend Interactivity

document.addEventListener('DOMContentLoaded', () => {
    // Attach loading states to all standard tool forms
    setupLoadingButtons();
});

function setupLoadingButtons() {
    const forms = [
        { formId: 'qaForm', btnId: 'qaSubmitBtn' },
        { formId: 'explainForm', btnId: 'explainSubmitBtn' },
        { formId: 'quizForm', btnId: 'quizSubmitBtn' },
        { formId: 'summarizeForm', btnId: 'summarizeSubmitBtn' },
        { formId: 'learnForm', btnId: 'learnSubmitBtn' }
    ];

    forms.forEach(({ formId, btnId }) => {
        const form = document.getElementById(formId);
        const btn = document.getElementById(btnId);
        if (form && btn) {
            form.addEventListener('submit', () => {
                const btnText = btn.querySelector('.btn-text');
                const btnSpinner = btn.querySelector('.btn-spinner');

                if (btnText && btnSpinner) {
                    btnText.style.display = 'none';
                    btnSpinner.style.display = 'inline-block';
                }
                btn.disabled = true;
                // Allow standard form submission to proceed
                form.submit();
            });
        }
    });
}
