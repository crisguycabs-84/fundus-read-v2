BEGIN;
INSERT INTO Modelo (modelo_id, nombre) VALUES
  (0, 'Ensemble'),
  (1, 'MobileNetV3Large'),
  (2, 'EfficientNetB0'),
  (3, 'ConvNeXtTiny');
COMMIT;
