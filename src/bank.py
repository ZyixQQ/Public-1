''''''

from models import Database, Bank, User

db = Database('bank_manage.db')

b = Bank(db, 1)

user = b.verify_user('Berat', 'beratbaba1', is_admin=True)
print(user)

print(user.accounts)

ac = user.get_accounts(1)
print(b.users)
print(b.get_usernames())

user._prepare()





