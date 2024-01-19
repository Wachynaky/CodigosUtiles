# Conversión de Texto a Voz en Español 

Cpmando que llama a la API de audio de OpenAI y pasa el texto a voz en español

Se ejecuta desde la línea de comandos 

## Código del Script

```bash
#!/bin/bash

# convierte de texto a voz en Español de manera eficaz


# URL de la API de OpenAI
API_URL="https://api.openai.com/v1/audio/speech"

# Tu clave de API de OpenAI
API_KEY="tu_clave_api_aquí"

#Texto de entrada que será convertido a voz
Texto='El otro día realicé una presentación en el Seonthebeach (el mejor evento SEO en mi opinión), que podemos dividir en dos partes. En la primera parte expliqué algunos comandos en el terminal de linux y cómo se podrían aprovechar para fines SEO, en los próximos artículos mostraré más ejemplos. En la segunda parte mostré un caso de uso un poco más complejo para crear un buscador de contenidos dentro de los vídeos de Youtube.En este post voy a detallar la segunda parte, cómo podemos utilizar la línea de comandos + python(Bert) + SQL para crear un buscador de contenidos dentro de los vídeos.Cómo expliqué en la presentación, además de los comandos nativos de linux, existen multitud de software fácilmente instalable que también podemos ejecutar desde la línea de comandos, para este ejemplo en concreto vamos a ver el programa yt-dlp mediante el cual obtendremos las transcripciones de cada vídeo de lista de reproducción en Youtube, y obtendremos estas transcripciones en español. yt-dlp tiene una infinidad de posibilidades, como podemos ver aquí, nosotros usaremos solamente alguna de ellas. En este caso, lo primero que necesitamos es extraer el id o URL de cada uno de los vídeos de la lista de reproducción de youtube y para ello podemos usar este comando: con el parámetro También nos interesa dividir este texto en diferentes párrafos, ya que luego añadiremos una fila en nuestra tabla de la base de datos con el contenido de cada uno para poder buscar de manera más concreta qué parte de qué vídeos responden a una determinada consulta, además, también nos valdrá para poder leer más fácilmente el contenido de cada vídeo. Vamos a usar una expresión regular para dividir el texto de cada vídeo en frases creando un salto de línea cuando encontremos la etiqueta seguida de una letra en mayúscula. Las transcripciones de Youtube pone en mayúsculas cuándo hay un punto y seguido o un punto y aparte (que en el vídeo o cuando hablamos en una breve pausa entre oriaciones) para dividir la transcripción en párrafos. Algo curioso es que si el vídeo es original en inglés y obtenemos la transcripción en español que ha sido generada automáticamente por Youtube, Estos puntos y aparte, mayúsculas y otras puntuaciones del texto también serán transcritas, mientras que si el vídeo es oiriginal en español, no obtendremos estos punto y aparte, y en muchas ocasiones no pone en mayúscula la primera letra de cada oración.....'


# Ejecutar el comando curl para generar el archivo de audio
curl "$API_URL" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "'"${Texto}"'",
    "voice": "alloy"
  }' \
  --output datos/ejemplo-salida-texto-a-voz.mp3

```
 Los audios con las diferentes voces los puedes ver desde aquí:
 
 > Con voz tipo Allow: [./datos/ejemplo-salida-texto-a-voz.mp3](./datos/ejemplo-salida-texto-a-voz.mp3)
 
 > Con voz tipo Echo: [./datos/ejemplo-salida-texto-a-voz-Echo.mp3](./datos/ejemplo-salida-texto-a-voz-Echo.mp3)
 
 > Con voz tipo Fable: [./datos/ejemplo-salida-texto-a-voz-Fable.mp3](./datos/ejemplo-salida-texto-a-voz-Fable.mp3)
 
