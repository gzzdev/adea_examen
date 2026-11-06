# INE Extractor

CLI para procesar imágenes de credenciales INE. Usa PaddleOCR para leer CURP y clave de elector, `zxing-cpp` para el QR del reverso y genera un registro JSON con auditoría CSV. Las conexiones a Oracle y SQL Server son opcionales.

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

El comando escribe `registros.json` y `audit.csv`. El campo `qr_reverso` queda en `null` cuando el código no se puede leer. Para guardar recortes de diagnóstico:

```bash
python -m app.main --input ./imagenes --output ./resultados --save-debug-images
```

## Persistencia opcional

Por defecto se escribe la auditoría en CSV y no se conecta a ninguna base.
Configurando `.env` y activando `ORACLE_ENABLED` o `SQLSERVER_ENABLED` se habilita la persistencia por base de datos. En ese caso instalar también `oracledb` o `pyodbc` según corresponda.
