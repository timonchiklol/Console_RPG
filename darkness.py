# imports
from random import randint

#база, не трогать
start = False
gold = 0
magic_1lvl = 0
magic_2lvl = 0
level = 0
health_points = 0
damage = randint(1,10)

# User_place это место на котором сейчас находится игрок
User_place = "menu"

def race():
    race = input("Race options: Human, Elf ")
    if race == "Human":
        health_points = 15
        level = 1
        gold = 5
        damage = randint(2,7)
        
    elif race == "Elf":
        health_points = 10
        level = 1
        gold = 5
        damage = randint(1,12)

    else:
         print("I dont understand:(")



def menu():
    print("start")
    print("about") 
    print("exit")
    menu_input = input()
    if menu_input == "start":
        return "вот тут надо чтобы нейросетка начинала генерить"
        start = True
    elif menu_input == "exit":
        exit()
    elif menu_input == "about":
        print("Nothing is here yet")
    else:
         print("I dont understand:(")
while True:
    menu()
    if start == True:
        race()
        