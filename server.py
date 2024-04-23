from fastapi import FastAPI, Request, HTTPException, Depends
from pymongo.mongo_client import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
from datetime import date
load_dotenv()
from pydantic import BaseModel, Field
from bson.objectid import ObjectId
import aioredis
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

RATE_LIMIT = os.getenv('RATE_LIMIT')
redis_pool = None


#Created Redis Pool Function
async def get_redis_pool():
    global redis_pool
    if redis_pool is None:
        redis_pool = await aioredis.create_redis_pool(os.getenv('REDIS_URL'))
    return redis_pool

app.dependency(get_redis_pool)


# Better if we implement this as feature flag instead of normal functionality as if there is any issue we just need to disable the flag to revert back to normal previous build
@app.middleware
async def feature_add_rate_limit(request:Request, call_next, redis_pool: aioredis.Redis = Depends()):
    #Added feature flag for this rate limiting feature
    if os.getenv("FEATURE_RATE_LIMITING") == "OFF" or os.getenv('FEATURE_RATE_LIMITING') == None:
        call_next(request)

    # Fetch UserID from request headers
    user_id = request.headers.get('user_id')

    user_data = await redis_pool.get(user_id)

    # Condition to check if there is no user_data or the date is already crossed span of one day, -> This will decrease the time complexity of overall process, as we will not clear the data as a whole from redis pool after the day ends.
    if user_data == None or user_data["date"] != str(date.today()):
        user_data = json.dumps({"current_calls": 0, "date":str(date.today())})
        redis_pool.set(user_id,user_data)
        
    if user_data["current_calls"]>=RATE_LIMIT:
        return {
            "message":"API LIMIT EXCEEDED"
        }
    
    user_data["current_calls"] += 1
    
    redis_pool.set(user_id, json.dumps(user_data))
    redis_pool.set(user_id, user_data)

    response = await call_next(request)
    return response



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

    
