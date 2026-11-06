CREATE TABLE IF NOT EXISTS expediente (
    id CHAR(36) NOT NULL,
    lote_id CHAR(36) NOT NULL,
    archivo VARCHAR(512) NOT NULL,
    hash_archivo CHAR(64) NOT NULL,
    estado VARCHAR(32) NOT NULL,
    curp CHAR(18) NULL,
    clave_elector CHAR(18) NULL,
    qr_reverso TEXT NULL,
    nombre_completo JSON NULL,
    domicilio JSON NULL,
    datos_electorales JSON NULL,
    mensaje_error TEXT NULL,
    intentos SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    creado_en DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    iniciado_en DATETIME(6) NULL,
    terminado_en DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_expediente_hash (hash_archivo),
    KEY ix_expediente_lote_estado (lote_id, estado),
    KEY ix_expediente_hash (hash_archivo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS log_auditoria (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    expediente_id CHAR(36) NULL,
    lote_id CHAR(36) NOT NULL,
    archivo VARCHAR(512) NULL,
    estado VARCHAR(32) NOT NULL,
    mensaje TEXT NULL,
    creado_en DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY ix_log_lote_fecha (lote_id, creado_en),
    KEY ix_log_expediente_fecha (expediente_id, creado_en),
    CONSTRAINT fk_log_expediente
        FOREIGN KEY (expediente_id) REFERENCES expediente (id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
