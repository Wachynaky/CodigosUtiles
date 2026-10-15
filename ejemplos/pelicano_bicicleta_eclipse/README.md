# Pelícano en bicicleta durante un eclipse

La ilustración se genera directamente con un único SELECT de ClickHouse y `FORMAT PNG`, siguiendo el mecanismo del README del repositorio. No necesita tablas, imágenes de entrada, UDFs ni código externo para renderizar.

El pelícano pedalea sobre el río. La escena incluye una bicicleta con radios, ondas en los puntos de contacto, reflejos, montañas, juncos y un eclipse de Sol próximo al horizonte.

Desde este directorio:

```bash
clickhouse local \
  --output_format_image_width 1600 \
  --output_format_image_height 1000 \
  --param_SAMPLES 4 \
  --queries-file queries/pelicano_bicicleta_eclipse.sql \
  > images/pelicano_bicicleta_eclipse.png
```

La consulta es una ilustración procedural en 2D con distancias a curvas de Bézier, elipses, anillos y polígonos. La luz de la corona solar, los reflejos y las ondas también se calculan en SQL. `numbers_mt` genera las muestras de los píxeles; `GROUP BY pixel` promedia el antialiasing; las columnas `r, g, b, x, y` se escriben con `FORMAT PNG`.

Para cambiar la resolución, mantén la proporción 8:5. `SAMPLES=1` ofrece una vista previa rápida; `SAMPLES=4` produce la imagen final. Verificado con ClickHouse local 26.9.19.9.

## Origen

Generado con Codex (sesión del 15 de octubre de 2026). El transcript completo de la sesión está exportado en [`../pelican_river_eclipse.html`](../pelican_river_eclipse.html). El único script Python que intervino (`fix_scope.py`) fue un parche temporal para renombrar variables de las lambdas de la SQL; la propia sesión lo borró tras aplicarlo, así que el resultado final es solo la consulta de `queries/`.

## Contenido

- `queries/pelicano_bicicleta_eclipse.sql`: la consulta completa (un único SELECT con `FORMAT PNG`).
- `images/pelicano_bicicleta_eclipse.png`: render final a 1600 x 1000 con `SAMPLES=4`.
- `images/preview.png`: vista previa a 640 x 400 con `SAMPLES=1`.
