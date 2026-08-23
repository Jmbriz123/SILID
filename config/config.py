import os 
from dotenv import load_dotenv
from sqlalchemy.engine import URL
load_dotenv() #load env variables to the environemt
#get environment variables
DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST") or "postgres"
DB_PORT = int(os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or "5432")
DB_NAME = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or "postgres"
DB_USER = os.getenv("DB_USER") or os.getenv("POSTGRES_USER") or "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or "postgres"

#contruct DB url from the variables 
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)
