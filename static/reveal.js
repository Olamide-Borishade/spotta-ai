// Scroll-reveal for homepage sections. Skips entirely if the user prefers reduced motion,
// since the CSS also neutralizes .reveal in that case (defense in depth).
(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const sections = document.querySelectorAll(".reveal");
  if (!sections.length) return;

  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) entry.target.classList.add("in");
      });
    },
    { threshold: 0.15 }
  );

  sections.forEach(function (el) {
    observer.observe(el);
  });
})();
