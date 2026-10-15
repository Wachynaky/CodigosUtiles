# Pelícano en bicicleta sobre el río, bajo un eclipse de Sol

Ilustración procedural renderizada íntegramente por un único `SELECT` de ClickHouse con `FORMAT PNG`. El generador en Python solo construye la geometría vectorial (3849 primitivas: elipses, cápsulas, polígonos, anillos y halos) y un índice espacial por teselas; ClickHouse calcula cada píxel: cobertura de formas, degradados, corona del eclipse, ondas del río, reflejo distorsionado de la bicicleta, transparencias, antialiasing y grano fino. No necesita tablas, UDFs, fuentes ni imágenes de entrada.

![Pelícano en bicicleta sobre el río bajo un eclipse](images/pelican_river_eclipse.png)

La escena incluye un pelícano articulado con plumas individuales y bolsa del pico sombreada; una bicicleta con radios cruzados, cadena, bielas, pedales, frenos y faro; espuma y gotas en los puntos de contacto con el agua; crestas montañosas lejanas, árboles en la orilla y juncos en primer plano.

## Contenido

- `generators/gen_pelican.py`: describe la escena y emite la consulta SQL. Solo usa la biblioteca estándar de Python.
- `generators/render_pelican.sh`: genera la SQL y lanza ClickHouse. Argumentos opcionales: ancho, alto, muestras y ruta de salida. Solo sustituye el PNG de destino si ClickHouse termina bien.
- `queries/pelican_river_eclipse.sql`: la consulta generada, autocontenida (unos 970 KB). Renderizarla solo requiere ClickHouse.
- `images/pelican_river_eclipse.png`: render final a 2400 x 1500 con 4 muestras por píxel.
- `renders/pelican_preview.png` y `renders/pelican_review.png`: vistas previas a 800 x 500 y 1200 x 750 que la sesión generó para revisar la composición.
- `exportado-claude-scope/trace-1-01a13f5c.html`: transcript completo de la sesión que creó el ejemplo, exportado desde Claude Scope. Se puede ver renderizado en [htmlpreview](https://htmlpreview.github.io/?https://raw.githubusercontent.com/Wachynaky/CodigosUtiles/main/ejemplos/pelican_river_eclipse/exportado-claude-scope/trace-1-01a13f5c.html).

## Reproducir

```bash
python3 generators/gen_pelican.py > queries/pelican_river_eclipse.sql
clickhouse local --max_query_size 10000000 \
                 --output_format_image_width 2400 --output_format_image_height 1500 \
                 --param_SAMPLES 4 --queries-file queries/pelican_river_eclipse.sql \
                 > images/pelican_river_eclipse.png
```

`--max_query_size` es necesario porque la consulta supera el tamaño por defecto; hay que pasarlo en la línea de comandos, antes de que se analice la consulta.

O bien, desde este directorio:

```bash
bash generators/render_pelican.sh                                   # 2400 x 1500, SAMPLES=4
bash generators/render_pelican.sh 800 500 1 renders/pelican_preview.png  # vista previa rápida
```

La composición usa proporción 8:5 sobre un lienzo de 1600 x 1000; otras proporciones cambian el encuadre. La resolución y las muestras son parámetros de ejecución, la escena queda fijada al generar la SQL.

## Origen

Generado con Codex el 15 de octubre de 2026 (sesión iniciada a las 13:39) sobre una copia del proyecto RayTracer (un trazador de rayos escrito en ClickHouse SQL, licencia CC BY-NC-SA 4.0). Verificado con ClickHouse local 26.9.19.9. El fichero SQL de este directorio es exactamente el que produce `gen_pelican.py`.

Una versión anterior de este mismo ejemplo, con otro generador y una SQL más sencilla, está en [`../pelican_river_eclipse-Opus`](../pelican_river_eclipse-Opus).
