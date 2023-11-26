"""NOT COMPLETED"""

from models import Session
import os
from getpass import getpass 
from exceptions import IncorrectOptionError
from currency import get_currencies
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
                if choice > len(self.options) - 1:
                    raise IncorrectOptionError('|| ! Enter a valid number.')
            except ValueError as e:
                input('|| ! Enter a valid number')
            except IncorrectOptionError as error:
                input(error)
            else:
                selected_option = self.options[[x[0] for x in self.options].index(int(choice))]
                selected_action = selected_option[2]
                if not hasattr(selected_action, 'options') and selected_action.__name__ == 'menu_closer':
                    selected_action(self) 
                    if self.name == 'ONLINE':
                        session.logout()
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
            user_info = '// ~ {id} >< {name} >< {email} > {notification}'
            notification = session.payload['message']
            header_string = user_info.format(id=session.user.user_id, name=session.user.username, email=session.user.email, notification=notification)
            print(title, header_string, sep='\n')
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
                            (1, 'Send Message', send_message_interface),
                            (2, 'View Messages', view_messages),
                            (3, 'Delete Message', delete_messages),
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
                         (4, 'Switch Banks', bank_choice_interface),
                         (0, 'Exit', Menu.menu_closer)
                         )
        online_menu = Menu('ONLINE',
                           (1, 'Account Operations', account_menu),
                           (2, 'Transfer Operations', transfer_menu),
                           (3, 'Session Operations', session_menu),
                           (4, 'Message Operations', message_menu),
                           (0, 'Log out', Menu.menu_closer)
                           )


def send_message_interface():       
    type_choices = {**session.database.message_types, 0: 'Back to menu'}
    if len(session.bank.users) == 1:
        input('|| ! There is no user you can send message')
        return
    
    def print_users():
        print(f'\\\\{SEP}\n|| Send Message:\n||{SEP}')
        print(*[f'|| {user[1]}: {user[0]}' for user in session.bank.users if user[1] != session.user.user_id])
    
    def print_type_choices():
        print(f'||{SEP}\n|| Message Types:')
        print(*[f'|| {message_num}: {message_type}'
              for message_num, message_type
              in type_choices.items()])
   
    def print_users_accounts():
        print(f'||{SEP}\n|| Your accounts:')
        for account in session.user.accounts.values():
            print(f'|| {account}', end='')
    
    try:
        print_users()
        receiver_id = int(input('|| Enter the user id you want to send message: '))
        print_type_choices()
        type_choice = int(input('|| Choose a message type -> ')) 
        if type_choice == 0:
            return
        if type_choice not in (1, 2):
            raise IncorrectOptionError('|| ! Please choose a correct type.')
        if not session.bank.does_user_exist(receiver_id) or receiver_id == session.user.user_id:
            raise IncorrectOptionError('|| ! You cannot send a message to yourself or to a non-existing user.')

    except ValueError:
        input('|| ! Invalid Choices. Please make sure you enter the values correctly.')
        return
   
    except IncorrectOptionError as error:
        input(error)
        return
    else:
        if type_choice == 1:
            message = input(f'||\n|| Enter your message--> ')
            session.send_message('message',
                                 {'message': message},
                                 receiver_id
                                 )                      
            input('|| + Message sent successfully.')
        
        elif type_choice == 2:
            print_users_accounts()
            
            try:
                account_id = int(input('\n|| Select an account id for your request: '))
                amount = int(input('|| Enter the amount: '))
                
                if session.user.accounts.get(account_id) == None:
                    raise IncorrectOptionError(f'|| ! You dont have an account with this id.')
                
                message = input('||\n|| Enter the message --> ')
            except ValueError:
                input('|| ! Invalid input. Please make sure you enter the values correctly.')
                return
            
            except IncorrectOptionError as error:
                input(error)
                return
            else:
                session.send_message('request',
                                     {'amount': amount,
                                      'account_id': account_id,
                                      'currency_code': session.user.accounts.get(account_id).currency_code,
                                      'message': message
                                      },
                                     receiver_id
                                     )
                input('|| + Message sent successfully.')





            
def print_messages(message=None):
        print(f'||{SEP}')
        if not message:
            for message_id, message in session.user.messages.items():
                info, user_message = message[-1].split('Message:')
                print(f'|| Type: {message[4]} |Id: {message_id} |Sender : {message[3]} |Date: {message[-2]}\n|| {info}\n|| Message: {user_message}')
                print(f'||{SEP}')
        else:
            info, user_message = message[-1].split('Message:')
            print(f'|| Selected Message: ')
            print(f'|| Type: {message[4]} |Id: {message[0]} |Sender : {message[3]} |Date: {message[-2]}\n|| {info}\n|| Message: {user_message}')
            print(f'||{SEP}')
            

def view_messages():
    session.payload['message'] = ''
    if len(session.user.messages) == 0:
        input(f'||{SEP}\n|| ! You dont have any messages.')
        return
    def choose_account():
        print(f'||{SEP}\n|| Your Accounts: ||', end='')
        for account in session.user.accounts.values():
            print(f'{account} <> ', end='')
        
        try:
            account_id = int(input('\n|| Choose an account id ->' ))
            
            if session.user.accounts.get(account_id) == None:
                raise IncorrectOptionError('|| ! You dont have an account with this id.')
        
        except ValueError:
            input('|| ! Please enter valid id.')
            return
        
        except IncorrectOptionError as error:
            input(error)
            return
        else:
            return account_id
    
    def examine_message(message):
        print_messages(message)
        
        if message[4] == 'request':
            print('|| Accept Request [1]\n|| Reject Request [2]\n|| Delete Message [3]\n|| Cancel Selection [0]')
            choice = input('|| --> ')
            
            if choice == '1':
                selected_account = choose_account()
                return None if selected_account is None else session.accept_request(message[0], selected_account)
                input(f'|| ! Request {message[0]} accepted succesfully')
            elif choice == '2':
                session.reject_request(message[0])
                input(f'|| ! Request {message[0]} succesfully rejected.')
            elif choice == '3':
                session.user.delete_message([message[0]])
                input(f'|| ! Message {message[0]} succesfully deleted.')
        else:
            print('|| Delete Message [1]\n|| Cancel Choice [0]')
            choice = input('|| --> ')
            
            if choice == '1':
                session.user.delete_message([message[0]])
                
       
    while True:
        Menu.header('MESSAGES')
        print(f'\\\\{SEP}\n|| Manage Messages: ')
        print_messages()
        
        try:
            selected_message = int(input(f'|| Enter message id for select (0 for back)-> '))
            if selected_message == 0:
                break
            elif selected_message not in session.user.messages:
                raise IncorrectOptionError(f'|| ! Invalid id please enter valid message id')
        except ValueError:
            input('|| ! Please enter valid number')
        except IncorrectOptionError as error:
            input(error)
        else:
            examine_message(session.user.messages.get(selected_message))
        

def print_currencies(currency_list):
    for i, x in enumerate(currencies):
        if i % 11 == 0 and i != 0:
            print(f'|| {x}')
        else:
            print(f'|| {x}', end='')
                        
            
def create_account():
    print(f'\\\\{SEP}\n|| Create Account:\n||{SEP}')
    currencies = list(get_currencies().keys())
    print_currencies(currencies)
    while True:
        chosen_currency = input('||\n|| Choose a currency_code for your new account --> ').upper()
    
        if chosen_currency in currencies:
            try:
                session.create_account(chosen_currency)
                input('|| + Account successfully created.')
                break
            except ValueError:
                input('|| ! You have reached the limit number of accounts.')
                break
        else:
            input('|| ! Invalid currency code.')
    
    
def delete_messages():
    print_messages()
    if len(session.user.messages) == 0:
        input('|| ! You dont have any messages.')
        return
    print(f"|| Enter all the message ids you want to delete with a space between them. i.e (1 21 34 483). To go back, just type 0.")
    while True:
        valid_ids = []
        message_ids = input(f'||{SEP}\n|| -> ')
        if message_ids.strip() == '0':
            break
        for message_id in message_ids.split():
            if message_id.isdigit() and int(message_id) in session.user.messages:
                valid_ids.append(int(message_id))
        if valid_ids:
            print(f'|| {valid_ids}')
            decision = input(f'|| Are you sure want to delete these messages (1 to accept) --> ')
            if decision == '1':
                session.user.delete_message(valid_ids)
                input('|| + Messages succesfully deleted.')
                break
            else:
                input('|| Deletion is canceled')
                
        else:
            input('|| ! You have not entered a valid id.')
                
        
        
        
                
            
def print_accounts(account=None):
    print(f'||{SEP}\n|| Owner ID || Account ID || Balance || Currency Code || Creation Date\n||{SEP}')
    if not account:
        for account in session.user.accounts.values():
            print(f'|| {account}')
    else:
        print(account)
        
    
def view_accounts():
    print_accounts()
    def account_options(account):
        print_accounts(account)
        print('|| Change Currency [1]\n|| Delete Account [2]\n|| Cancel Selection [0]')
        choice = input('|| --> ')
        if choice == '1':
            currencies = list(get_currencies().keys())
            print_currencies(currencies)
            chosen_currency = input('|| Choose a currency --> ')
            if chosen_currency in currencies:
                session.user.change_account_currency(account.account_id, change_account_currency)
        elif choice == '2':
            ...
        else:
            return
        
    while True: 
        try:
            selected_account_id = int(input('|| Enter the account id for select --> '))
            if selected_account_id not in session.user.accounts:
                raise IncorrectOptionError('|| ! You dont have an account with this id')
        except ValueError:
            input('|| ! Enter valid number')
        except IncorrectOptionError as error_message:
            input(error_message)
        else:
            account_options(session.user.accounts.get(selected_account_id))
     
        
    
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


                

def bank_choice_interface():
    while True:
        Menu.header('START')
        print(rf'\\{SEP}')
        for bank_id, bank_name in session.database.banks.items():
            print(f'|| {bank_name} >< Id: {bank_id}')
        print(f'||{SEP}')
        
        try:
            bank_id = int(input('|| Choose a bank id -> '))
            if bank_id not in session.database.banks.keys():
                raise ValueError('Invalid number')
        except ValueError:
            input('|| ! Please enter a valid bank id.')
        else:
            session.connect_bank(bank_id)
            break
    



