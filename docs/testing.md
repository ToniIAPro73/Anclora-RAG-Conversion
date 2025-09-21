# Guía de pruebas

Este repositorio incorpora pruebas automatizadas que verifican el flujo completo
de conversión e ingesta de documentos, incluyendo la preservación de metadatos
originales antes y después de ejecutar normalizaciones NFC.

## Ejecutar toda la suite

```bash
make test
```

El objetivo `test` invoca a `pytest` y ejecuta todas las pruebas, incluidas las
marcadas como `slow`, que simulan pipelines completos con agentes y wrappers de
herramientas de terceros.

## Ejecutar únicamente las pruebas del conversor

```bash
make test-converter
```

Este objetivo limita la ejecución a `tests/converter`, que contiene fixtures de
ejemplo en `tests/converter/fixtures/` para validar el comportamiento de los
pipelines de ingesta.

## Filtrar por marcador

Las pruebas de pipelines están etiquetadas como `slow`. Para ejecutarlas de
forma aislada, utiliza:

```bash
pytest -m slow
```

Si deseas excluirlas durante desarrollos rápidos puedes usar `pytest -m "not slow"`.
