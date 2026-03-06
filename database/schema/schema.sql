CREATE TABLE Clase (
 clase_id VARCHAR(36) NOT NULL,
 nombre CHAR(20)
);

ALTER TABLE Clase ADD CONSTRAINT PK_Clase PRIMARY KEY (clase_id);


CREATE TABLE Escalafon (
 escalafon_id SMALLINT NOT NULL,
 nombre VARCHAR(50) NOT NULL
);

ALTER TABLE Escalafon ADD CONSTRAINT PK_Escalafon PRIMARY KEY (escalafon_id);


CREATE TABLE Imagenes (
 img_id VARCHAR(36) NOT NULL,
 url VARCHAR(500),
 clase_id VARCHAR(36) NOT NULL
);

ALTER TABLE Imagenes ADD CONSTRAINT PK_Imagenes PRIMARY KEY (img_id);


CREATE TABLE Modelo (
 modelo_id SMALLINT NOT NULL,
 nombre VARCHAR(50) NOT NULL
);

ALTER TABLE Modelo ADD CONSTRAINT PK_Modelo PRIMARY KEY (modelo_id);


CREATE TABLE ModoLectura (
 modo_id SMALLINT NOT NULL,
 nombre VARCHAR(20)
);

ALTER TABLE ModoLectura ADD CONSTRAINT PK_ModoLectura PRIMARY KEY (modo_id);


CREATE TABLE Usuarios (
  user_id VARCHAR(36) NOT NULL,
  email VARCHAR(150) NOT NULL,
  cc VARCHAR(50) NOT NULL,
  telefono VARCHAR(20),
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  role VARCHAR(20) NOT NULL DEFAULT 'reader',
  escalafon_id SMALLINT NOT NULL,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ NULL,
  last_login_at TIMESTAMPTZ NULL,
  CONSTRAINT PK_Usuarios PRIMARY KEY (user_id),
  CONSTRAINT UQ_Usuarios_email UNIQUE (email),
  CONSTRAINT FK_Usuarios_0
    FOREIGN KEY (escalafon_id)
    REFERENCES "Escalafon"(escalafon_id)
);


CREATE TABLE Gradcam (
 grad_id VARCHAR(36) NOT NULL,
 url VARCHAR(500),
 clase2_id VARCHAR(36) NOT NULL,
 clase1_id VARCHAR(36) NOT NULL,
 modelo_id SMALLINT NOT NULL,
 img_id VARCHAR(36) NOT NULL
);

ALTER TABLE Gradcam ADD CONSTRAINT PK_Gradcam PRIMARY KEY (grad_id);


CREATE TABLE Lecturas (
 lectura_id VARCHAR(36) NOT NULL,
 posicion INT NOT NULL,
 start TIMESTAMP WITH TIME ZONE,
 done TIMESTAMP WITH TIME ZONE,
 modo_id SMALLINT NOT NULL,
 user_id VARCHAR(36) NOT NULL,
 img_id VARCHAR(36) NOT NULL,
 diagnostico_clase_id VARCHAR(36) NOT NULL
);

ALTER TABLE Lecturas ADD CONSTRAINT PK_Lecturas PRIMARY KEY (lectura_id);


ALTER TABLE Imagenes ADD CONSTRAINT FK_Imagenes_0 FOREIGN KEY (clase_id) REFERENCES Clase (clase_id);

ALTER TABLE Gradcam ADD CONSTRAINT FK_Gradcam_0 FOREIGN KEY (clase2_id) REFERENCES Clase (clase_id);
ALTER TABLE Gradcam ADD CONSTRAINT FK_Gradcam_1 FOREIGN KEY (clase1_id) REFERENCES Clase (clase_id);
ALTER TABLE Gradcam ADD CONSTRAINT FK_Gradcam_2 FOREIGN KEY (modelo_id) REFERENCES Modelo (modelo_id);
ALTER TABLE Gradcam ADD CONSTRAINT FK_Gradcam_3 FOREIGN KEY (img_id) REFERENCES Imagenes (img_id);


ALTER TABLE Lecturas ADD CONSTRAINT FK_Lecturas_0 FOREIGN KEY (modo_id) REFERENCES ModoLectura (modo_id);
ALTER TABLE Lecturas ADD CONSTRAINT FK_Lecturas_1 FOREIGN KEY (user_id) REFERENCES Usuarios (user_id);
ALTER TABLE Lecturas ADD CONSTRAINT FK_Lecturas_2 FOREIGN KEY (img_id) REFERENCES Imagenes (img_id);
ALTER TABLE Lecturas ADD CONSTRAINT FK_Lecturas_3 FOREIGN KEY (diagnostico_clase_id) REFERENCES Clase (clase_id);


