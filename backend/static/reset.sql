/*
Reset global (todos los usuarios y modos)
*/

BEGIN;

UPDATE public.lecturas
SET
  start = NULL,
  done  = NULL,
  diagnostico_clase_id = 'Pendiente';

COMMIT;

/*
Reset por usuario
*/

BEGIN;

UPDATE public.lecturas
SET
  start = NULL,
  done  = NULL,
  diagnostico_clase_id = 'Pendiente'
WHERE user_id = 'r_10';

COMMIT;

/*
Reset por usuario + modo
*/

BEGIN;

UPDATE public.lecturas
SET
  start = NULL,
  done  = NULL,
  diagnostico_clase_id = 'Pendiente'
WHERE user_id = 'r_10'
  AND modo_id = 0;

COMMIT;