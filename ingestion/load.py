#Take the records output by API extraction and commin them as raw JSONB to PostgreSQL(bronze.weather_raw)
import os 
import logging
import psycopg2
from psycopg2.extras import Json
from ingestion.extract import run_extraction_batch
from config.config import DATABASE_URL

#configure logging system 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )
#get logger for this module 
logger = logging.getLogger(__name__)

def load_extracted_records_to_bronze(records: list[dict]):
    """
    Insert  raw city API payloads into the bronze.weather_raw table 
    """
    insert_query = """
        INSERT INTO bronze.weather_raw (city_key, city_name, ingested_at, raw_payload)
        VALUES (%s, %s, %s, %s)
    """
    try:
        #load data into bronze table
        connection_parameters = {
            "host": DATABASE_URL.host,
            "port": DATABASE_URL.port,
            "dbname": DATABASE_URL.database,
            "user": DATABASE_URL.username,
            "password": DATABASE_URL.password,
        }
        with psycopg2.connect(**connection_parameters) as connection:
            with connection.cursor() as cursor:
                #insert each record to bronze table
                for record in records:
                    cursor.execute(insert_query,
                    (record["city_key"], record["city_name"], record["ingested_at"], Json(record["raw_payload"]))
                    )
                connection.commit()
                logger.info("Load %d records into bronze.weather_raw table", len(records))
    except Exception as e:
        logger.error("Failed loading data to Bronze layer")
        raise

if __name__ == "__main__":
    data = run_extraction_batch()
    load_extracted_records_to_bronze(data)