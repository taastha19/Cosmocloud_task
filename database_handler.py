from fastapi import FastAPI, Request, HTTPException
from pymongo.mongo_client import MongoClient
app= FastAPI()
from dotenv import load_dotenv
import os
load_dotenv()
from pydantic import BaseModel, Field
from bson.objectid import ObjectId

class Address(BaseModel):
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country")

class Student(BaseModel):
    name: str = Field(..., description="Name")
    age: int = Field(..., description="Age")
    address: Address = Field(..., description="Address")

def getCollectionInstance():
    MONGODB_URL = os.getenv('CONNECTION_STRING')
    client = MongoClient(MONGODB_URL)

    db = client["student_db"]

    if 'student_data' not in db.list_collection_names():
        db.create_collection('student_data')

    collections = db['student_data']

    return collections


