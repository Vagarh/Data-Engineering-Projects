-- init.sql
-- Crear base de datos para el Data Warehouse 
CREATE DATABASE dw_portafolio;

\c dw_portafolio;

-- Extensiones útiles para geometría (postgis) no siempre necesarias si solo usamos lat/lon
-- En este caso lo guardaremos plano para máxima simplicidad, pero guardamos las coordenadas.

CREATE TABLE IF NOT EXISTS public.accidentes_transito (
    id SERIAL PRIMARY KEY,
    fecha_accidente DATE,
    hora_accidente TIME,
    gravedad_accidente VARCHAR(100),
    clase_accidente VARCHAR(100),
    lugar_accidente VARCHAR(255),
    comuna VARCHAR(100),
    barrio VARCHAR(100),
    latitud NUMERIC(10, 6),
    longitud NUMERIC(10, 6),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (fecha_accidente, hora_accidente, latitud, longitud) -- Evitar duplicados exactos
);

CREATE INDEX idx_fecha_accidente ON public.accidentes_transito (fecha_accidente);
CREATE INDEX idx_comuna ON public.accidentes_transito (comuna);
