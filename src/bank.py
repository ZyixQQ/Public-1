"""NOT COMPLETED"""

from models import Session
import os
from getpass import getpass 

t_width, t_height = os.get_terminal_size()

session = Session(db_path='bank_manage.db')




def clear_terminal():
    os.system('clear') if os.name == 'posix' else os.system('cls')
    


def header(menu_name: str):
    clear_terminal()
    title = f'+{"-"*9}{menu_name}{"-"*(t_width - 10 - len(menu_name))}'
    
    if session.user is not None:    
        user_info = f'|> {session.user.user_id} >< {session.user.username} >< {session.user.email}\n+{"-"*20}'
        print(title, user_info, sep='\n')
    else:
        print(title)
        print(f'|> Not login yet\n+{"-"*20}')
        
        




def login_menu():
    print('|/-'*10)
    username = input('| Username @-> ')
    password = getpass('| Password !-> ')
    response = session.login(username, password)
    input(response[1])
    
        




def online_menu():
    while True:
        header('ONLINE')
        print('''\
|-  1 <> Account Operations
|-  2 <> Transfer Operations
|-  3 <> Session Operations
|-  0 <> Logout
|>------------<''')
        match input('|-->'):
            case '1':
                account_menu()
            case '2':
                transfer_menu()
            case '3':
                session_menu()
            case '0':
                session.logout()
                break

        

def main_menu():
    while True:
        header('OFFLINE')
        print('''\
|-  1 <> Login
|-  2 <> Sign Up
|-  3 <> See Bank Status
|-  0 <> Exit
|>-----------<''')
        match input('|--> '):
            case '1':
                login_menu()
            case '2':
                register_menu()
            case '3':
                bank_status_menu()
            case '0':
                break
        if session.user is not None:
            online_menu()
        
                
                








