# Pelícano en bicicleta sobre el río, bajo un eclipse de Sol

Ilustración procedural renderizada íntegramente por un único `SELECT` de ClickHouse con `FORMAT PNG`: corona solar, agua, reflejos, radios, plumas, salpicaduras y antialiasing. El generador en Python solo describe la geometría (campos de distancia 2D por capas) y emite la SQL; ClickHouse calcula cada píxel y codifica el PNG. No necesita tablas, UDFs ni imágenes de entrada.

![Pelícano en bicicleta sobre el río bajo un eclipse](images/pelican_river_eclipse.png)

## Contenido

- `generators/gen_pelican.py`: describe la escena y emite la consulta SQL. Solo usa la biblioteca estándar de Python.
- `generators/render_pelican.sh`: genera la SQL y lanza ClickHouse. Argumentos opcionales: ancho, alto, muestras y ruta de salida.
- `queries/pelican_river_eclipse.sql`: la consulta generada, autocontenida. Renderizarla solo requiere ClickHouse.
- `images/pelican_river_eclipse.png`: render final a 2400 x 1500 con 4 muestras por píxel.

## Reproducir

```bash
python3 generators/gen_pelican.py > queries/pelican_river_eclipse.sql
clickhouse local --output_format_image_width 2400 --output_format_image_height 1500 \
                 --param_SAMPLES 4 --queries-file queries/pelican_river_eclipse.sql \
                 > images/pelican_river_eclipse.png
```

O bien, desde este directorio:

```bash
bash generators/render_pelican.sh            # 2400 x 1500, SAMPLES=4
bash generators/render_pelican.sh 800 500 1  # vista previa rápida
```

La composición está diseñada para 16:10 sobre un lienzo de 1600 x 1000; otras proporciones cambian el encuadre horizontal. La resolución y las muestras son parámetros de ejecución, la escena queda fijada al generar la SQL.

## Origen

Generado con Codex el 15 de octubre de 2026 sobre una copia del proyecto RayTracer (un trazador de rayos escrito en ClickHouse SQL, licencia CC BY-NC-SA 4.0). Verificado con ClickHouse local 26.9.19.9. El fichero SQL de este directorio es exactamente el que produce `gen_pelican.py`.
