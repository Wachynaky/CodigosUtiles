# Conversión de Texto a Voz en Español

Este script convierte texto a voz en español de manera eficaz. El audio de salida se puede obtener [aquí](./datos/ejemplo-salida-texto-a-voz.mp3).

## Código del Script

```bash
#!/bin/bash

# convierte de texto a voz en Español de manera eficaz
# El audio de salida se puede obtener aquí: ./datos/ejemplo-salida-texto-a-voz.mp3

# URL de la API de OpenAI
API_URL="https://api.openai.com/v1/audio/speech"

# Tu clave de API de OpenAI
API_KEY="tu_clave_api_aquí"

# Crear el directorio 'datos' si no existe
mkdir -p datos

# Ejecutar el comando curl para generar el archivo de audio
curl "$API_URL" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "El otro día realicé una presentación en el Seonthebeach (el mejor evento SEO en mi opinión), que podemos dividir en dos partes.",
    "voice": "alloy"
  }' \
  --output datos/ejemplo-salida-texto-a-voz.mp3
