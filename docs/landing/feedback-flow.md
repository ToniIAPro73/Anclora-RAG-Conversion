# Flujo de feedback y analítica ligera

Este documento describe cómo se gestionan los formularios y el seguimiento de interacción en la landing page de Anclora AI (`docs/landing/`).

## Formularios habilitados

La landing incluye tres formularios basados en [Netlify Forms](https://docs.netlify.com/forms/setup/):

1. **`demo-form`** – Solicitudes de demostración y evaluación de piloto.
2. **`waitlist-form`** – Lista de espera para actualizaciones de producto y lanzamientos.
3. **`feedback-form`** – Investigación de necesidades y descubrimiento de problemas.

Cada formulario:

- Usa la propiedad `data-netlify="true"` para que Netlify capture los envíos.
- Incluye un `honeypot` (`bot-field`) para reducir spam automatizado.
- Muestra mensajes de éxito/error gestionados en `assets/js/feedback.js`.

### Flujo operativo sugerido

1. **Publicación en Netlify**
   - Desplegar el sitio estático (`docs/landing/`) en un sitio Netlify (por ejemplo `landing.anclora.ai`).
   - Mantener activada la opción *Forms* en la configuración del proyecto.

2. **Almacenamiento y notificaciones**
   - En Netlify, activar notificaciones por correo a `growth@anclora.ai` para cada nuevo envío.
   - Configurar un _outgoing webhook_ hacia el endpoint de automatización de Slack (`https://hooks.slack.com/services/...`) para avisar en el canal `#anclora-leads`.
   - Conectar la integración con Airtable/Notion mediante Zapier o n8n para registrar los campos clave (`name`, `email`, `company`, `volume`, `message`).

3. **Asignación de responsables**
   - **Ventas (demo-form):** el equipo comercial recibe alertas y debe contactar en < 24 h.
   - **Producto (feedback-form):** el equipo de producto clasifica la retroalimentación semanalmente y la etiqueta según tipo de desafío.
   - **Marketing (waitlist-form):** marketing alimenta una secuencia de correos (bienvenida, roadmap, invitaciones a webinars).

### Manejo de errores

Si Netlify no está disponible, el script `feedback.js` muestra el mensaje de error con la dirección de contacto correspondiente para que la persona usuaria pueda escribir directamente.

## Analítica ligera

Se utiliza [Plausible Analytics](https://plausible.io/) con el script `script.manual.pageview-props.js`, configurado con el dominio `landing.anclora.ai`.

### Eventos capturados

- **Pageview** manual: el script puede invocarse desde `feedback.js` (ejemplo de evento personalizado `Formulario enviado`).
- **Formularios**: al completarse un formulario, se dispara `window.plausible('Formulario enviado', { props: { form: '<nombre>' } })` para segmentar conversiones.

### Recomendaciones de privacidad

- Activar la opción *Self-Hosted Proxy* de Plausible o usar el proxy oficial para cumplir con GDPR.
- Actualizar la política de privacidad con el detalle de uso de formularios y analítica.

## Monitoreo de métricas

| Métrica | Fuente | Frecuencia | Responsable |
| --- | --- | --- | --- |
| Conversiones demo | Evento Plausible `Formulario enviado` (prop `demo-form`) | Semanal | Ventas |
| Nuevos leads lista de espera | Netlify + CRM | Diario | Marketing |
| Feedback cualitativo | Exportación Netlify → Notion | Quincenal | Producto |
| Fallos de formulario | Alertas Netlify (webhook) | En tiempo real | Ingeniería |

## Próximos pasos sugeridos

- Conectar Plausible con el dashboard ejecutivo ya utilizado por el equipo.
- Evaluar herramientas complementarias (Hotjar, LogRocket) solo si se mantiene el enfoque en privacidad.
- Añadir tracking de CTA secundarias mediante atributos `data-analytics` y eventos manuales.
