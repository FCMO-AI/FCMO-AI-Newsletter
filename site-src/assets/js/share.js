(() => {
  for (const button of document.querySelectorAll('[data-copy]')) {
    button.addEventListener('click', async () => {
      const field = document.getElementById(button.dataset.copy);
      if (!field) return;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(field.value);
      } catch (_) {
        field.focus();
        field.select();
        try { document.execCommand('copy'); } catch (__) { return; }
      }
      button.textContent = button.dataset.done || original;
      setTimeout(() => { button.textContent = original; }, 2000);
    });
  }
})();
