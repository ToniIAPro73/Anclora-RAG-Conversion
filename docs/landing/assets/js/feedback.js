(function () {
  const forms = document.querySelectorAll('form[data-netlify="true"]');

  const encode = (data) =>
    Object.keys(data)
      .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
      .join('&');

  forms.forEach((form) => {
    const success = form.querySelector('[data-success]');
    const error = form.querySelector('[data-error]');

    if (success) success.style.display = 'none';
    if (error) error.style.display = 'none';

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const data = {};
      formData.forEach((value, key) => {
        data[key] = value;
      });

      try {
        await fetch('/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: encode(data),
        });

        if (success) {
          success.style.display = 'block';
          success.setAttribute('role', 'status');
        }
        if (error) {
          error.style.display = 'none';
        }
        form.reset();

        if (window.plausible) {
          const eventName = form.getAttribute('name') || 'form-submit';
          window.plausible('Formulario enviado', { props: { form: eventName } });
        }
      } catch (err) {
        console.error('Error submitting Netlify form', err);
        if (error) {
          error.style.display = 'block';
          error.setAttribute('role', 'alert');
        }
        if (success) {
          success.style.display = 'none';
        }
      }
    });
  });
})();
