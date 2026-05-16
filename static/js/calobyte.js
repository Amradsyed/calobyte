/* ── CaloByte JS ── */

// Sticky navbar scroll effect
(function () {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;
  const onScroll = () => {
    if (window.scrollY > 20) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  };
  window.addEventListener('scroll', onScroll, { passive: true });
})();

// Mobile menu toggle
(function () {
  const btn = document.getElementById('mobile-menu-btn');
  const menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;
  btn.addEventListener('click', () => {
    menu.classList.toggle('open');
    btn.setAttribute('aria-expanded', menu.classList.contains('open'));
  });
})();

// Animate progress bars on page load
(function () {
  document.querySelectorAll('.progress-fill[data-width]').forEach(bar => {
    requestAnimationFrame(() => {
      bar.style.width = bar.dataset.width + '%';
    });
  });
})();

// Newsletter subscribe (prevent default, show feedback)
(function () {
  const form = document.getElementById('newsletter-form');
  if (!form) return;
  form.addEventListener('submit', e => {
    e.preventDefault();
    const input = form.querySelector('input[type="email"]');
    const btn = form.querySelector('button');
    if (input && input.value) {
      btn.textContent = '✓ Subscribed!';
      btn.style.background = 'linear-gradient(135deg, #34d399, #059669)';
      input.value = '';
      setTimeout(() => {
        btn.textContent = 'Subscribe';
        btn.style.background = '';
      }, 3000);
    }
  });
})();

// Flash message auto-dismiss
(function () {
  document.querySelectorAll('.flash-message').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      el.style.transition = 'opacity 0.4s, transform 0.4s';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });
})();

// Intersection Observer for fade-in-up on scroll
(function () {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.scroll-reveal').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });
})();