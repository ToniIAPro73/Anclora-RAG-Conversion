# Cumplimiento GDPR y CCPA

Este documento describe cómo Anclora AI RAG implementa controles de privacidad
para cumplir con los principios de **minimización**, **limitación de
propósitos** y **derechos de los titulares de los datos** establecidos en GDPR y
CCPA. Las prácticas aquí documentadas son de obligatorio cumplimiento para el
equipo de operaciones y para cualquier socio tecnológico que interactúe con el
sistema.

## Roles y responsabilidades

| Rol | Responsable | Funciones clave |
| --- | ----------- | --------------- |
| Responsable de Privacidad | Oficial de Protección de Datos (DPO) | Validar políticas, aprobar solicitudes de sujetos y coordinar auditorías externas. |
| Líder Técnico de RAG | Arquitecto de Plataforma | Mantener los módulos de ingestión y borrado, validar registros de auditoría y publicar actualizaciones técnicas. |
| Operaciones / Soporte | Equipo de Operaciones 24/7 | Recibir solicitudes, ejecutar el flujo de derecho al olvido y documentar incidentes. |
| Seguridad de la Información | CISO | Revisar controles de acceso, monitorear anomalías y garantizar el resguardo de logs. |

## Flujo del derecho al olvido

1. **Recepción**: la solicitud llega por el portal de privacidad, correo o
   canal interno. El Operador genera un ticket (ej. `GDPR-001`).
2. **Validación**: el DPO confirma la identidad del solicitante y verifica que
   la información esté dentro del alcance de Anclora AI RAG.
3. **Ejecución**:
   - Se invoca el endpoint `POST /privacy/forget` o el comando interno con el
     identificador del archivo y el `subject_id` asociado.
   - El módulo `PrivacyManager` elimina referencias en ChromaDB, purga archivos
     temporales (incluyendo staging `documents/` y `tempfile.gettempdir()`),
     anonimiza metadatos y escribe un registro de auditoría en
     `logs/privacy_audit.log`.
4. **Verificación**:
   - El Operador revisa el log para confirmar el `audit_id` generado y valida
     que las colecciones y archivos eliminados coinciden con el alcance de la
     solicitud.
   - Se ejecutan pruebas automatizadas (`pytest tests/test_privacy.py`) cuando
     haya cambios en los pipelines de ingestión o privacidad.
5. **Confirmación**: se notifica al solicitante compartiendo el identificador
   de auditoría y la fecha de cumplimiento.

## Checklists operativos

### Antes de cargar datos (responsable: Líder Técnico de RAG)

- [ ] Revisar contratos de tratamiento y bases legales para nuevos datasets.
- [ ] Garantizar que los archivos fuente estén rotulados con el dominio correcto
      (`documents`, `code`, `multimedia`).
- [ ] Validar que los metadatos sensibles estén anonimizados o pseudonimizados
      antes de la ingesta.

### Al recibir una solicitud de derecho al olvido (responsable: Operaciones)

- [ ] Confirmar identidad del solicitante junto con el DPO.
- [ ] Registrar ticket con canal, fecha y `subject_id`.
- [ ] Ejecutar `POST /privacy/forget` con el `filename` exacto y metadatos
      asociados.
- [ ] Verificar el `audit_id` y adjuntarlo al ticket.
- [ ] Cerrar la solicitud con evidencia (capturas de log y respuesta del
      endpoint).

### Auditoría mensual (responsable: Seguridad de la Información)

- [ ] Revisar `logs/privacy_audit.log` en busca de anomalías o accesos fuera de
      horario.
- [ ] Validar integridad y retención de logs (mínimo 12 meses).
- [ ] Confirmar que las pruebas automáticas de privacidad se ejecutaron en el
      pipeline de CI.
- [ ] Informar hallazgos al DPO y definir acciones correctivas.

## Matriz de comunicación

- **Incidente o brecha**: notificar de inmediato al CISO y al DPO. Activar el
  plan de respuesta y registrar los eventos en menos de 24 horas.
- **Consultas de usuarios finales**: canalizar vía Operaciones. Responder en un
  máximo de 72 horas con el estado del caso.
- **Cambios en la normativa**: el DPO actualiza este documento y convoca a
  capacitación obligatoria al resto de los roles.

## Evidencia y trazabilidad

- Todos los registros generados por `PrivacyManager` deben almacenarse con
  control de acceso de solo lectura para Operaciones y lectura/escritura para el
  DPO.
- El repositorio debe incluir pruebas unitarias que verifiquen la eliminación de
  datos (ver `tests/test_privacy.py`).
- El equipo técnico debe conservar evidencia de las ejecuciones exitosas de
  `pytest` y de los despliegues que afecten el pipeline de datos.

