import json
import os

USERS_FILE = 'users.json'

class User:
    def __init__(self, username, password, privilege):
        self.username = username
        self.password = password
        self.privilege = privilege

    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

    def get_privilege(self):
        return self.privilege


class LoginSystem:
    def __init__(self):
        self.current_user = None
        self.initialize_users_file()

    def run(self):
        while True:
            print("\n=== Login System ===")
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            choice = input("Choose an option: ")

            if choice == '1':
                self.register_user()
            elif choice == '2':
                self.login_user()
            elif choice == '3':
                print("Exiting...")
                break
            else:
                print("Invalid option!")

            if self.current_user:
                self.show_user_menu()

    def initialize_users_file(self):
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'w') as file:
                json.dump({}, file)

    def load_users(self):
        try:
            with open(USERS_FILE, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}

    def save_users(self, users):
        try:
            with open(USERS_FILE, 'w') as file:
                json.dump(users, file, indent=4)
        except Exception as e:
            print(f"Error saving users: {e}")

    def register_user(self):
        print("\n--- Registration ---")
        username = input("Enter username: ").strip()

        users = self.load_users()
        if username in users:
            print("Username already exists!")
            return

        password = input("Enter password: ")
        print("\nSelect account type:")
        print("1. Tenant (Privilege 1)")
        print("2. Property Owner (Privilege 2)")
        print("3. Admin (Privilege 3)")
        account_type = input("Enter choice: ")

        if account_type not in {'1', '2', '3'}:
            print("Invalid account type!")
            return

        users[username] = {
            "password": password,
            "privilege": int(account_type)
        }
        self.save_users(users)
        print("Registration successful!")

    def login_user(self):
        print("\n--- Login ---")
        username = input("Enter username: ").strip()
        password = input("Enter password: ")

        users = self.load_users()
        if username not in users:
            print("User not found!")
            return

        user_data = users[username]
        if user_data["password"] == password:
            self.current_user = User(username, password, user_data["privilege"])
            print("Login successful!")
            print(f"Welcome, {username}!")
            print(f"Account type: {self.get_account_type_name(user_data['privilege'])}")
        else:
            print("Incorrect password!")

    def show_user_menu(self):
        while self.current_user:
            print("\n--- User Menu ---")
            print("1. View Profile")
            print("2. Logout")
            if self.current_user.get_privilege() == 3:
                print("3. List All Users")
            choice = input("Choose an option: ")

            if choice == '1':
                self.view_profile()
            elif choice == '2':
                self.current_user = None
                print("Logged out successfully!")
            elif choice == '3' and self.current_user.get_privilege() == 3:
                self.list_all_users()
            else:
                print("Invalid option!")

    def view_profile(self):
        print("\n--- Your Profile ---")
        print(f"Username: {self.current_user.get_username()}")
        print(f"Account Type: {self.get_account_type_name(self.current_user.get_privilege())}")
        print(f"Privilege Level: {self.current_user.get_privilege()}")

    def list_all_users(self):
        users = self.load_users()
        print("\n--- All Users ---")
        for username, data in users.items():
            privilege = data["privilege"]
            print(f"Username: {username} | Type: {self.get_account_type_name(privilege)} | Privilege: {privilege}")

    def get_account_type_name(self, privilege):
        return {
            1: "Tenant",
            2: "Property Owner",
            3: "Admin"
        }.get(privilege, "Unknown")


if __name__ == "__main__":
    login_system = LoginSystem()
    login_system.run()
