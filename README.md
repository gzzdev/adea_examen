# INE Extractor

CLI para procesar imágenes de credenciales INE. Usa PaddleOCR para leer CURP y clave de elector, `zxing-cpp` para el QR del reverso y genera un registro JSON con auditoría CSV o MariaDB.

## Estructura

```text
app/
  main.py                     CLI y escritura de resultados
  config.py                   Variables de entorno
  services/
    extraction_service.py     Flujo de extracción por imagen
    repositories.py           Auditoría y persistencia
  vision/
    preprocessing.py          Lectura, perspectiva
    roi.py                    Detección, normalización y recortes
    face_classifier.py        Orientación y clasificación de las caras
    qr_reader.py              Decodificación del QR
  ocr/
    paddle_engine.py          Lector PaddleOCR
  parsing/
    curp.py                   Validación y extracción de CURP
    clave_elector.py          Extracción de clave de elector
    ine_fields.py             Nombre, domicilio y datos electorales
    catalogs.py               Catálogos de validación
  models/
    results.py                Resultado de extracción
tests/                        Pruebas con valores sintéticos
```

Antes de extraer campos, el flujo detecta rectángulos con proporción de credencial, separa una composición con ambas caras, corrige perspectiva y orientación, y clasifica anverso/reverso por texto y QR. Los campos se ubican a partir de las cajas de las etiquetas dentro del anverso normalizado.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

PaddleOCR descarga sus modelos en la primera ejecución. El lector usa CPU con oneDNN desactivado para evitar un error de inferencia de PaddlePaddle 3.3.x.

## Ejecución

```bash
python -m app.main --input ./imagenes --output ./resultados
```

El procesamiento usa actores Ray con PaddleOCR precargado. Ajusta el número
de actores según la memoria disponible:

```bash
python -m app.main --input ./imagenes --output ./resultados --workers 2
```

El comando escribe `registros.json` y `audit.csv`. El campo `qr_reverso` queda en `null` cuando el código no se puede leer. Cada registro también incluye `nombre_completo`, `domicilio` y `datos_electorales`. Municipio y localidad quedan en `null` cuando no aparecen con una etiqueta legible; no se infieren a partir del estado. Para guardar recortes de diagnóstico:

```bash
python -m app.main --input ./imagenes --output ./resultados --save-debug-images
```

## Persistencia con MariaDB

Levantar la base de datos de desarrollo:

```bash
docker compose up -d mariadb
```

El esquema inicial se crea automáticamente en el primer arranque y define las tablas `expediente` y `log_auditoria`. Cada archivo se identifica mediante SHA-256; si la misma imagen ya existe, se registra como `DUPLICADO` y no se vuelve a ejecutar el OCR. Para habilitar la conexión desde la aplicación, configurar en `.env`:

```dotenv
DB_ENABLED=true
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=adea
DB_USER=adea
DB_PASSWORD=adea_dev_password
```

El volumen `mariadb_data` conserva la base entre reinicios. Los scripts de
`db/init` solo se ejecutan automáticamente cuando el volumen se crea por
primera vez; los cambios posteriores deben agregarse como nuevas migraciones.

Cuando `DB_ENABLED=false`, la auditoría se conserva en `audit.csv`; cuando se
activa, cada resultado y su evento se escriben en `expediente` y
`log_auditoria` de MariaDB.

## Tablero web

Con MariaDB activa y las variables `DB_*` configuradas, iniciar la interfaz de
consulta con:

```bash
flask --app app.web run --host 0.0.0.0 --port 8000
```

Abrir `http://localhost:8000`. El tablero muestra un resumen, los expedientes y
la tabla de auditoría. Incluye búsqueda, filtro por estado, paginación y una
vista de detalle para los datos extraídos. La interfaz es de solo lectura.
