-- Create isolated schemas for Medallion architecture
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Raw immutable ingestion table for Open-Meteo payloads
-- Tableas a historical append-only table to store raw JSON payloads from Open-Meteo API for each city
CREATE TABLE IF NOT EXISTS bronze.weather_raw (
    id BIGSERIAL PRIMARY KEY,  
    city_key VARCHAR(50) NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB NOT NULL --for that actual data carried in the Open-Meteo API response, stored as JSONB for flexibility and efficiency
);

-- Index to optimize latest-ingestion lookups per city
CREATE INDEX IF NOT EXISTS idx_bronze_city_ingested 
ON bronze.weather_raw (city_key, ingested_at DESC);


