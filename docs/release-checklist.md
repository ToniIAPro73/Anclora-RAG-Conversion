# Checklist de lanzamiento de la landing Anclora AI

> Objetivo: lanzar la landing (`docs/landing/`) en producción, habilitar feedback y monitorear rendimiento durante las primeras 4 semanas.

## 1. Preparación (T-14 días)

- [ ] Revisar copy y claims con equipo legal y compliance.
- [ ] Validar assets visuales (logo, colores, fuentes) con branding.
- [ ] Actualizar enlaces externos (LinkedIn, Calendario, Email) y verificar que estén activos.
- [ ] Configurar dominio `landing.anclora.ai` y certificado SSL.
- [ ] Aprobar política de privacidad y aviso de cookies actualizado.
- [ ] Confirmar responsables de seguimiento (Marketing, Producto, Ventas, Ingeniería).

## 2. QA previo al despliegue (T-7 días)

- [ ] Pruebas de visualización en navegadores clave (Chrome, Firefox, Safari, Edge) y mobile.
- [ ] Validar tiempos de carga (< 2.5s LCP en conexiones 4G) usando Lighthouse.
- [ ] Probar envíos de formularios `demo-form`, `waitlist-form` y `feedback-form` en entorno de staging.
- [ ] Confirmar recepción de notificaciones en correo, Slack y CRM.
- [ ] Revisar que los eventos de Plausible se registren correctamente.
- [ ] Ejecutar checklist de accesibilidad (contrast ratio, labels, navegación con teclado).

## 3. Go-Live (Día 0)

- [ ] Publicar la landing en Netlify o infraestructura elegida.
- [ ] Activar redirecciones necesarias (ej. `/beta`, `/demo`).
- [ ] Anunciar internamente (Slack/Notion) que la landing está en producción.
- [ ] Programar recordatorios diarios para revisar formularios durante la semana de lanzamiento.
- [ ] Hacer _smoke test_ post-deploy (carga, CTA, formularios, analytics).

## 4. Comunicación externa

- [ ] Enviar correo a lista de interesados con resumen del roadmap (ver plan en `docs/landing/roadmap-comunicacion.md`).
- [ ] Publicar anuncio en LinkedIn y Twitter corporativo.
- [ ] Compartir la landing con partners estratégicos y solicitar retroalimentación.
- [ ] Coordinar participación en comunidades relevantes (ej. Latam Startups, Product Hackers).

## 5. Monitoreo post-release (Semana 1-4)

- [ ] Revisar diariamente métricas clave (visitas únicas, conversiones demo, lista de espera).
- [ ] Analizar feedback cualitativo y generar insights semanales.
- [ ] Ajustar copy o secciones con base en comportamiento (scroll depth, heatmaps si aplica).
- [ ] Confirmar que no existan errores 404/500 mediante monitoreo de uptime (StatusCake/UptimeRobot).
- [ ] Actualizar dashboard de métricas compartido con stakeholders.
- [ ] Preparar informe de impacto al cierre de la semana 4.

## 6. Retrospectiva y siguientes iteraciones (Semana 5)

- [ ] Realizar retro con equipos involucrados (Marketing, Producto, Ventas, Ingeniería).
- [ ] Priorizar mejoras detectadas en backlog (`docs/backlog.md`).
- [ ] Documentar aprendizajes y actualizar checklist para próximos lanzamientos.

---

### Notas adicionales

- Mantener evidencia de aprobaciones en Notion o GDrive.
- Documentar cualquier excepción o riesgo identificado durante el proceso.
