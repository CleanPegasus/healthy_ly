from flask import Flask
import cv2
import numpy as np
import tensorflow as tf
#from tensorflow.keras.models import load_model
import requests
import json
from firebase import Firebase
from PIL import Image
import urllib


model = tf.keras.models.load_model('new_model.h5')


food_category = np.load('food_category.npy')

print(food_category.shape)

config = {
    "apiKey": "****************",
    "authDomain": "**************************",
    "databaseURL": "**************************",
    "storageBucket": "**************************"
}

firebase = Firebase(config)



def get_image():


    db = firebase.database()
    users = db.child("url").get()

    url = users.val()

    print(url)

    #response = requests.get(url)
    #print(BytesIO(response.content))
    #img = Image.open(urllib.request.urlopen(url))

    resp = urllib.request.urlopen(url)
    img = np.asarray(bytearray(resp.read()), dtype = "uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    img = img[483:3357, 2:2158]  

    img = cv2.resize(img, (128, 128))
    image = np.asarray(img)/255
    image = np.reshape(image, [-1, 128, 128, 3])

    return image

def predict():

    food_image = get_image()
    food = food_category[model.predict(food_image).argmax()]
    food = food.replace("_", " ")

    return food


def get_food_nutrients(food):
    url = "https://nutritionix-api.p.rapidapi.com/v1_1/search/{}".format(food)

    querystring = {"fields": "item_name,nf_calories,nf_total_fat"}

    headers = {
        'x-rapidapi-host': "nutritionix-api.p.rapidapi.com",
        'x-rapidapi-key': "***********************************"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    # print(response.text)

    output = response.json()

    calories = []
    fat = []

    hits = output["hits"]
    calories = hits[0]["fields"]["nf_calories"]
    fat = hits[0]["fields"]["nf_total_fat"]

    nutrients = {"calories": calories,
                 "fat": fat}

    # nutrients = json.dumps(res)

    return nutrients


def get_food_details(food):
    url = "https://recipe-puppy.p.rapidapi.com/"

    headers = {
        'x-rapidapi-host': "recipe-puppy.p.rapidapi.com",
        'x-rapidapi-key': "**********************************"
    }

    querystring = {"q": str(food)}

    response = requests.request("GET", url, headers=headers, params=querystring)

    output = response.json()

    # print(output['results'])
    ingredients = []
    names = []
    recepies = []

    for food in output['results']:
        content = food['ingredients'].split(',')
        names.append(food['title'])
        recepies.append(food['href'])
        ingredients = ingredients + content

    # res = dict(zip(names, recepies))

    # print(str(res))

    food_recipe = {"names": names,
                   "recepies": recepies,
                   "ingredients": ingredients}

    return food_recipe



def get_json(food):

    #food_recipe = get_food_details(food)
    #print(food_recipe)
    nutrients = get_food_nutrients(food)
    #print(nutrients)

    output = {"prediction" : food, **nutrients}

    #print(total_dict)

    #output = json.dumps(total_dict)

    return output


def send_data():
    
    food = predict()

    output = get_json(food)

    db = firebase.database()

    db.child("result/two").set(output)   

    return output


while(True):

    db = firebase.database()
    check_val = db.child("check").get().val()


    if(check_val == 1):

        output = send_data()
        print(output)

        db.child("check").set(0)
        

    
