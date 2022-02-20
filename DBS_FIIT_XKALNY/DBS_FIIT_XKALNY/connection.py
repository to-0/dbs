from dotenv import load_dotenv
import psycopg2
import os
load_dotenv()
conn = psycopg2.connect(dbname="dota2", user=os.environ["DB_USER"], password=os.environ["DB_PASS"], port=5432, host=os.environ["DB_HOST"])