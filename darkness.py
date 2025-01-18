

# User_place это место на котором сейчас находится игрок
User_place = "menu"



def menu():
    print("start")
    print("about") 
    print("exit")
    menu_input = input()
    if menu_input == "start":
        return "вот тут надо чтобы нейросетка начинала генерить"
    elif menu_input == "exit":
        exit()
    elif menu_input == "about":
        print("Nothing is here yet")
    else:
         print("I dont understand:(")
while True:
    menu()