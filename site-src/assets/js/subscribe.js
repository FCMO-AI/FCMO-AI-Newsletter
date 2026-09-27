(() => {
  "use strict";

  const links = document.querySelectorAll('a[data-ghost-portal="signup"]');
  if (!links.length || typeof HTMLDialogElement === "undefined") return;

  links.forEach((link) => {
    link.addEventListener("click", (event) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      const dialog = document.createElement("dialog");
      dialog.className = "portal-overlay";
      dialog.setAttribute("aria-label", link.dataset.portalTitle || link.textContent.trim());
      Object.assign(dialog.style, { width: "min(42rem, calc(100% - 2rem))", height: "min(48rem, calc(100% - 2rem))", padding: "1rem", border: "1px solid #0a0a0a" });

      const close = document.createElement("button");
      close.type = "button";
      close.className = "portal-overlay-close";
      close.textContent = link.dataset.portalClose || "Close";
      Object.assign(close.style, { display: "block", margin: "0 0 0.75rem auto", font: "inherit" });
      close.addEventListener("click", () => dialog.close());

      const frame = document.createElement("iframe");
      frame.className = "portal-overlay-frame";
      frame.title = link.dataset.portalTitle || link.textContent.trim();
      frame.src = link.href;
      Object.assign(frame.style, { width: "100%", height: "calc(100% - 5rem)", border: "0" });

      const fallback = document.createElement("a");
      fallback.className = "portal-overlay-fallback";
      fallback.href = link.href;
      fallback.rel = "external noopener";
      fallback.textContent = link.dataset.portalFallback || link.textContent.trim();
      Object.assign(fallback.style, { display: "inline-block", marginTop: "0.75rem" });

      dialog.append(close, frame, fallback);
      dialog.addEventListener("close", () => dialog.remove());
      document.body.append(dialog);

      try {
        dialog.showModal();
        event.preventDefault();
      } catch (_error) {
        dialog.remove();
      }
    });
  });
})();
