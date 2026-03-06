BEGIN;
INSERT INTO Usuarios (user_id, email, password, is_active, escalafon_id, nombre, pais) VALUES
  ('r_1', 'email1@correo.com', 'pass1', B'1', 1, 'nombre1', 'Venezuela'),
  ('r_2', 'email2@correo.com', 'pass2', B'1', 1, 'nombre2', 'Venezuela'),
  ('r_3', 'email3@correo.com', 'pass3', B'1', 1, 'nombre3', 'Venezuela'),
  ('r_4', 'email4@correo.com', 'pass4', B'1', 1, 'nombre4', 'Venezuela'),
  ('r_5', 'email5@correo.com', 'pass5', B'1', 2, 'nombre5', 'Colombia'),
  ('r_6', 'email6@correo.com', 'pass6', B'1', 2, 'nombre6', 'Colombia'),
  ('r_7', 'email7@correo.com', 'pass7', B'1', 2, 'nombre7', 'Colombia'),
  ('r_8', 'email8@correo.com', 'pass8', B'1', 2, 'nombre8', 'Colombia'),
  ('r_9', 'email9@correo.com', 'pass9', B'1', 3, 'nombre9', 'Colombia'),
  ('r_10', 'email10@correo.com', 'pass10', B'1', 3, 'nombre10', 'Colombia'),
  ('r_11', 'email11@correo.com', 'pass11', B'1', 3, 'nombre11', 'Colombia'),
  ('r_12', 'email12@correo.com', 'pass12', B'1', 3, 'nombre12', 'Colombia'),
  ('r_13', 'email13@correo.com', 'pass13', B'1', 4, 'nombre13', 'Colombia'),
  ('r_14', 'email14@correo.com', 'pass14', B'1', 4, 'nombre14', 'Colombia'),
  ('r_15', 'email15@correo.com', 'pass15', B'1', 4, 'nombre15', 'Colombia'),
  ('r_16', 'email16@correo.com', 'pass16', B'1', 4, 'nombre16', 'Colombia');
COMMIT;
