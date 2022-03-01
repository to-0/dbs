from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
# import psycopg2
# import os
# from dotenv import load_dotenv
# load_dotenv()
# conn = psycopg2.connect(dbname="dota2", user=os.environ["DB_USER"], password=os.environ["DB_PASS"], port=5432, host=os.environ["DB_HOST"])
from DBS_FIIT_XKALNY.connection import conn

def home(request):
    return HttpResponse("Test")

def health(request):
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION();")
    data = cursor.fetchall()
    columns = [des[0] for des in cursor.description]
    print("Columns", columns)
    print(cursor.description)
    print(type(data))
    cursor.execute(" SELECT pg_database_size('dota2')/1024/1024 as dota2_db_size;")
    print(cursor.description)
    columns += [des[0] for des in cursor.description]
    data += cursor.fetchall()
    print(data)
    print(data[0])
    response = {
        "pgsql": {
            columns[0]: ' '.join(data[0]),
            columns[1]: data[1][0]
        }
    }
    return JsonResponse(response)
