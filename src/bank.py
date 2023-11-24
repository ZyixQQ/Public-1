"""NOT COMPLETED"""

from models import Session
import os
from getpass import getpass 


t_width, t_height = os.get_terminal_size()
session = Session()
SEP = '>-----------------<'


class Menu:
    def __init__(self, name, *options):
        self.name = name
        self.options = options
        self.event = True
    
    def __call__(self): 
        self.event = True
        while self.event:
            self.header(self.name)
            self.display_options(*self.options)
            try:
                choice = int(input(r'||--> '))
            except ValueError as e:
                raise e
            else:
                selected_option = self.options[[x[0] for x in self.options].index(int(choice))]
                selected_action = selected_option[2]
                if not hasattr(selected_action, 'options') and selected_action.__name__ == 'menu_closer':
                    selected_action(self)
                else:
                    selected_action()
    
    def menu_closer(self):
        self.event = False
    
    @staticmethod
    def display_options(*options):
        print(r'\\' + SEP)
        for i, option in enumerate(options):
            prefix = '//' if i % 2 == 0 else r'\\'
            print(f'{prefix} - {option[0]} <> {option[1]}')
        print(r'\\' + SEP if len(options) % 2 == 1 else '//' + SEP)
            
    
    @staticmethod
    def header(menu_name: str):
        Menu.clear_terminal()
        title = f' {"_"*9}{menu_name}{"_"*(t_width - 10 - len(menu_name))}'
        
        if session.user is not None:    
            user_info = f'// ~ {session.user.user_id} >< {session.user.username} >< {session.user.email}'
            print(title, user_info, sep='\n')
        else:
            print(title)
            print(f'// ~ Not login yet')           
    
    @staticmethod
    def clear_terminal():
        os.system('clear') if os.name == 'posix' else os.system('cls')

    @staticmethod
    def starter():
        global account_menu
        global main_menu
        global transfer_menu
        global online_menu
        global message_menu
        message_menu = Menu('MESSAGES',
                            (1, 'Send Message', send_message),
                            (2, 'View Messages', view_messages),
                            (3, 'Delete Message', delete_message),
                            (0, 'Back to prev menu', Menu.menu_closer)
                            )
        transfer_menu = Menu('TRANSFERS',
                             (1, 'Make Transfer', make_transfer),
                             (2, 'View Transactions', view_transactions),
                             (0, 'Back to prev menu', Menu.menu_closer)
                             )
        account_menu = Menu('ACCOUNTS',
                            (1, 'Create Account', create_account),
                            (2, 'View Accounts', view_accounts),
                            (3, 'Delete Accounts', delete_account),
                            (0, 'Back to prev menu', Menu.menu_closer)
                            )
        main_menu = Menu('OFFLINE',
                         (1, 'Login', login_interface),
                         (2, 'Sign Up', register_interface),
                         (3, 'View Banks', bank_status_interface),
                         (4, 'Switch Banks', start_interface),
                         (0, 'Exit', Menu.menu_closer)
                         )
        online_menu = Menu('ONLINE',
                           (1, 'Account Operations', account_menu),
                           (2, 'Transfer Operations', transfer_menu),
                           (3, 'Session Operations', session_menu),
                           (4, 'Message Operations', message_menu),
                           (0, 'Log out', Menu.menu_closer)
                           )

        
def send_message():...
def view_messages():...
def delete_message():...
def create_account():...
def view_accounts():...
def delete_account():...
def make_transfer():...
def view_transactions():...
def session_menu():...



def login_interface():
    print(f'\\\\{SEP}\n|| Login :')
    username = input('|| Username @-> ')
    password = getpass('|| Password !-> ')
    response = session.login(username, password)
    input(response[1])
    if response[0]:
        online_menu()
           

def register_interface():
    print(f'//{SEP}\n|| Register :')
    username = input('|| Username (a-Z, 0-9) -> ')
    password = getpass('|| Password (^4, a-Z, 0-9) -> ')
    password_again = getpass('|| Password (again) -> ')
    email = input('|| Email -> ')
    if password == password_again:
        response = session.create_user(username, password, email)
        input(response[1])
    else:
        input('|| The passwords did not match. Please make sure the passwords are the same.')
    
    
def bank_status_interface():
    print(f'//{SEP}\n|| Bank Status :')
    print(f'|| ID: {session.bank.bank_id}\n|| Database: {session.database.db_path}')
    print(f'|| Users: {session.bank.users}')
    input(f'||\n\\\\ + Press Enter to continue: ')


                

def start_interface():
    Menu.header('START')
    print(rf'||{SEP}')
    for bank in session.database.banks:
        print(f'|| {bank[1]} >< Id: {bank[0]}')
    print(f'||{SEP}')
    bank_id = int(input('|| Choose a bank id -> '))
    session.connect_bank(bank_id)

Menu.starter()
start_interface()
main_menu()



# Previous Work
'''
def account_menu():
    while True:
        header('ACCOUNTS')
        Menu.display_options((1, 'Create Account'),
                        (2, 'View Accounts'),
                        (3, 'Delete Account'),
                        (0, 'Back to main menu')
                        )
        match input(r'\\--> '):
            case '1':
                ...
            case '2':
                ...
            case '3':
                ...
            case '0':   
                break
            
def transfer_menu():
    while True:
        header('Transactions')
'''    
'''
def online_menu():
    global menu_active
    menu_active = False
    while True:
        header('ONLINE')
        display_options((1, 'Account Operations'),
                        (2, 'Transfer Operations'),
                        (3, 'Session Operations'),
                        (4, 'Message Operations'),
                        (0, 'Logout')
                        )
        match input('//-->'):
            case '1':
                account_menu()
            case '2':
                transfer_menu()
            case '3':
                session_menu()
            case '4':
                message_menu()
            case '0':
                session.logout()
                break'''


'''
def main_menu():
    while True:
        header('OFFLINE')
        display_options((1, 'Login'), 
                        (2, 'Sign UP'), 
                        (3, 'View Bank Status'), 
                        (4, 'Switch Bank'), 
                        (0, 'Exit')
                        ) 
        match input('//--> '):
            case '1':
                login_menu()
            case '2':
                register_menu()
            case '3':
                bank_status_menu()
            case '4':
                start_menu()
            case '0':
                break
        if session.user is not None:
            online_menu()
 '''       