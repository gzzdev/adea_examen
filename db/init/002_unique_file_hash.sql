-- La misma imagen no debe volver a recibirse, aunque pertenezca a otro lote.
-- El bloque es idempotente para instalaciones nuevas y volúmenes existentes.
SET @old_key = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'expediente'
      AND index_name = 'uq_expediente_lote_hash'
);
SET @sql = IF(@old_key > 0,
    'ALTER TABLE expediente DROP INDEX uq_expediente_lote_hash',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @new_key = (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'expediente'
      AND index_name = 'uq_expediente_hash'
);
SET @sql = IF(@new_key = 0,
    'ALTER TABLE expediente ADD UNIQUE KEY uq_expediente_hash (hash_archivo)',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
