(() => {
  "use strict";
  // Ghost Portal owns the membership transaction. This first-party enhancement
  // adds an account-management route without intercepting the no-JS signup link.
  document.querySelectorAll('a[data-ghost-portal="signup"]').forEach((link) => {
    link.setAttribute("aria-label", link.textContent.trim());
  });
  document.querySelectorAll('form[data-email-form]').forEach((form) => {
    // Kit owns the confirmation. An opaque response proves only submission.
    // Other providers retain their ordinary, readable POST navigation.
    if (form.dataset.emailConfirmation !== 'opaque') return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!form.reportValidity() || form.dataset.busyNow === 'true') return;
      const section = form.closest('.sub-experience');
      const error = form.querySelector('[role="alert"]');
      const button = form.querySelector('button[type="submit"]');
      const label = button.textContent; const body = new FormData(form);
      const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 20000);
      error.hidden = true; form.dataset.busyNow = 'true'; section.dataset.state = 'busy';
      section.style.minHeight = section.getBoundingClientRect().height + 'px';
      button.disabled = true; button.textContent = form.dataset.busy; form.setAttribute('aria-busy', 'true');
      try {
        await fetch(form.action, { method: 'POST', body, mode: 'no-cors', credentials: 'omit', signal: controller.signal });
        section.dataset.state = 'pending'; section.querySelector('[data-sub-idle]').hidden = true;
        const pending = section.querySelector('[data-sub-pending]'); pending.hidden = false;
        pending.querySelector('[tabindex="-1"]').focus();
      } catch {
        section.dataset.state = 'error'; error.hidden = false; error.textContent = form.dataset.error;
      } finally {
        clearTimeout(timeout); delete form.dataset.busyNow; button.disabled = false;
        button.textContent = label; form.removeAttribute('aria-busy');
      }
    });
  });
})();
