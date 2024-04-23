from fastapi import FastAPI, Request, HTTPException
from pymongo.mongo_client import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
load_dotenv()
from pydantic import BaseModel, Field
from bson.objectid import ObjectId

from database_handler import Address, Student, getCollectionInstance
app= FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
UNIQUE_ID_NUMBER=0

collections=getCollectionInstance() 

# Completed
@app.head('/')
async def default_route():
    return {
        "message":"Welcome to my Server!"
    }
@app.get('/')
async def default_route():
    return {
        "message":"Welcome to my Server!"
    }
@app.post('/students')
async def readData(request: Student):
    try:
        result = collections.insert_one(request.model_dump())
        
        object_id = result.inserted_id
        print("RESULT",result,object_id,type(str(object_id)))
        return {
            "id":str(object_id)
        }
    except Exception as e:
        print("Something went wrong!")
        print(e)
        return {
            "id":"Something went wrong!"
        }

# Completed
@app.get('/students')
async def send_list_of_all_student():
    try:
        finalResult={
            "data":[
                
            ]
        }
        students = list(collections.find().limit(1000))
        for item in students:
            finalResult["data"].append({
                "name": item["name"],
                "age":item["age"]
            })
        print(students)
        return finalResult
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something wen wrong")



#Completed
@app.get('/students/{id}',response_description="Get a single student",
    response_model=Student,
    response_model_by_alias=False)
async def get_student(id):
    try:
        document = collections.find_one({"_id": ObjectId(id)})
        if document==None:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if document:
            return document
        return ""
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something wen wrong")
        
    

# Completed
@app.delete('/students/{id}')
async def delete_student(id):
    try:
        collections.find_one_and_delete({"_id":ObjectId(id)})
        return {}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something wen wrong")



@app.patch('/students/{id}')
async def update_student(id, parameters : Request):
    try:
        existing_item = collections.find_one({"_id": ObjectId(id)})
        
        if existing_item is None:
            raise HTTPException(status_code=404, detail="Item not found")

        update_dict = await parameters.json()
        copy_of_existing_item = existing_item

        # Helper recursive function to update fields in update_dict without affecting other fields
        def Helper_updating_item(current_Dictionary,to_update):
            for item in to_update:
                print(type(to_update[item]))
                if str(type(to_update[item]))=="<class 'dict'>":
                    Helper_updating_item(current_Dictionary[item],to_update[item])
                else:
                    current_Dictionary[item]=to_update[item]
        Helper_updating_item(existing_item,update_dict)
         
        # Validating if new doc fullfilling the base criteria
        Student(**existing_item)

        collections.replace_one({"_id":ObjectId(id)},existing_item)
        return {}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something wen wrong")

    
