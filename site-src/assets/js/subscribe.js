(() => {
  "use strict";
  // Ghost Portal owns the membership transaction. This first-party enhancement
  // adds an account-management route without intercepting the no-JS signup link.
  document.querySelectorAll('a[data-ghost-portal="signup"]').forEach((link) => {
    link.setAttribute("aria-label", link.textContent.trim());
  });
})();
