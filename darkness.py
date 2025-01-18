# imports
from random import randint
from gemini import Gemini
from dotenv import load_dotenv
import os
load_dotenv()
# глобальные переменные
start = False
gold = 0
magic_1lvl = 0
magic_2lvl = 0
level = 0
health_points = 0
damage = randint(1,10)
player_race = ""
player_class = ""

google_api_key = os.getenv("GEMINI_API_KEY")

#промпт для Ai
gemini = Gemini(google_api_key,system_instruction="Continue the story from DnD based on the following user input and your answers before. Keep it engaging and creative, and continue in one sentence also make battles every 3 user inputs. and read specifecation in the code 8-16 line of code")

# User_place это место на котором сейчас находится игрок
User_place = "menu"

def choose_race():
    global health_points, level, gold, damage, player_race
    player_race = input("Race options: Human, Elf ")
    if player_race == "Human":
        health_points = 15
        level = 1
        gold = 5
        damage = randint(2,7)
        
    elif player_race == "Elf":
        health_points = 10
        level = 1
        gold = 5
        damage = randint(1,12)
    else:
        print("I dont understand:(")
        choose_race()

def choose_class():
    global health_points, gold, magic_1lvl, player_class
    player_class = input("Class options: Warrior, Mage, Ranger ")
    if player_class == "Warrior":
        health_points = health_points + 5
        gold = gold + 2
        magic_1lvl = 0
        
    elif player_class == "Mage":
        health_points = health_points + 2
        gold = gold + 1
        magic_1lvl = 2
        
    elif player_class == "Ranger":
        health_points = health_points + 3
        gold = gold + 3
        magic_1lvl = 1
        
    else:
        print("I dont understand:(")
        choose_class()

def menu():
    global start
    print("start")
    print("about") 
    print("exit")
    menu_input = input()
    if menu_input == "start":
        start = True
    elif menu_input == "exit":
        exit()
    elif menu_input == "about":
        print("Nothing is here yet")
        menu()
    else:
        print("I dont understand:(")
        menu()

menu()
if start:
    choose_race()
    choose_class()
    print("The tavern buzzes with life, laughter, and clinking tankards. A cloaked figure enters, their boots heavy on the wooden floor, and all eyes turn to them. They approach your table, drop a sealed parchment, and say, You're needed for something...")
while True:
    print(gemini.send_message(input()))