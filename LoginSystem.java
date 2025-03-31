import java.io.*;
import java.util.*;
import org.json.simple.*;
import org.json.simple.parser.*;

public class LoginSystem {
    private static final String USERS_FILE = "users.json";
    private User currentUser;
    private JSONParser parser = new JSONParser();

    public static void main(String[] args) {
        LoginSystem loginSystem = new LoginSystem();
        loginSystem.run();
    }

    public void run() {
        Scanner scanner = new Scanner(System.in);
        initializeUsersFile();

        while (true) {
            System.out.println("\n=== Login System ===");
            System.out.println("1. Register");
            System.out.println("2. Login");
            System.out.println("3. Exit");
            System.out.print("Choose an option: ");

            int choice = scanner.nextInt();
            scanner.nextLine(); // consume newline

            switch (choice) {
                case 1:
                    registerUser(scanner);
                    break;
                case 2:
                    loginUser(scanner);
                    break;
                case 3:
                    System.out.println("Exiting...");
                    return;
                default:
                    System.out.println("Invalid option!");
            }

            if (currentUser != null) {
                showUserMenu(scanner);
            }
        }
    }

    private void initializeUsersFile() {
        File file = new File(USERS_FILE);
        if (!file.exists()) {
            try (FileWriter writer = new FileWriter(USERS_FILE)) {
                writer.write("{}");
            } catch (IOException e) {
                System.err.println("Error creating users file: " + e.getMessage());
            }
        }
    }

    @SuppressWarnings("unchecked")
    private void registerUser(Scanner scanner) {
        System.out.println("\n--- Registration ---");
        System.out.print("Enter username: ");
        String username = scanner.nextLine().trim();

        JSONObject users = loadUsers();
        if (users.containsKey(username)) {
            System.out.println("Username already exists!");
            return;
        }

        System.out.print("Enter password: ");
        String password = scanner.nextLine();

        System.out.println("\nSelect account type:");
        System.out.println("1. Tenant (Privilege 1)");
        System.out.println("2. Property Owner (Privilege 2)");
        System.out.println("3. Admin (Privilege 3)");
        System.out.print("Enter choice: ");
        int accountType = scanner.nextInt();
        scanner.nextLine(); // consume newline

        if (accountType < 1 || accountType > 3) {
            System.out.println("Invalid account type!");
            return;
        }

        JSONObject newUser = new JSONObject();
        newUser.put("password", password);
        newUser.put("privilege", accountType);

        users.put(username, newUser);
        saveUsers(users);

        System.out.println("Registration successful!");
    }

    private void loginUser(Scanner scanner) {
        System.out.println("\n--- Login ---");
        System.out.print("Enter username: ");
        String username = scanner.nextLine().trim();

        System.out.print("Enter password: ");
        String password = scanner.nextLine();

        JSONObject users = loadUsers();
        if (!users.containsKey(username)) {
            System.out.println("User not found!");
            return;
        }

        JSONObject user = (JSONObject) users.get(username);
        String storedPassword = (String) user.get("password");
        long privilege = (long) user.get("privilege");

        if (storedPassword.equals(password)) {
            currentUser = new User(username, password, (int) privilege);
            System.out.println("Login successful!");
            System.out.println("Welcome, " + username + "!");
            System.out.println("Account type: " + getAccountTypeName((int) privilege));
        } else {
            System.out.println("Incorrect password!");
        }
    }

    private void showUserMenu(Scanner scanner) {
        while (currentUser != null) {
            System.out.println("\n--- User Menu ---");
            System.out.println("1. View Profile");
            System.out.println("2. Logout");
            
            // Admin-specific options
            if (currentUser.getPrivilege() == 3) {
                System.out.println("3. List All Users");
            }
            
            System.out.print("Choose an option: ");
            int choice = scanner.nextInt();
            scanner.nextLine(); // consume newline

            switch (choice) {
                case 1:
                    viewProfile();
                    break;
                case 2:
                    currentUser = null;
                    System.out.println("Logged out successfully!");
                    return;
                case 3:
                    if (currentUser.getPrivilege() == 3) {
                        listAllUsers();
                    } else {
                        System.out.println("Invalid option!");
                    }
                    break;
                default:
                    System.out.println("Invalid option!");
            }
        }
    }

    private void viewProfile() {
        System.out.println("\n--- Your Profile ---");
        System.out.println("Username: " + currentUser.getUsername());
        System.out.println("Account Type: " + getAccountTypeName(currentUser.getPrivilege()));
        System.out.println("Privilege Level: " + currentUser.getPrivilege());
    }

    @SuppressWarnings("unchecked")
    private void listAllUsers() {
        JSONObject users = loadUsers();
        System.out.println("\n--- All Users ---");
        
        for (Object key : users.keySet()) {
            String username = (String) key;
            JSONObject user = (JSONObject) users.get(username);
            long privilege = (long) user.get("privilege");
            
            System.out.println("Username: " + username + 
                               " | Type: " + getAccountTypeName((int) privilege) +
                               " | Privilege: " + privilege);
        }
    }

    private String getAccountTypeName(int privilege) {
        switch (privilege) {
            case 1: return "Tenant";
            case 2: return "Property Owner";
            case 3: return "Admin";
            default: return "Unknown";
        }
    }

    private JSONObject loadUsers() {
        try (FileReader reader = new FileReader(USERS_FILE)) {
            return (JSONObject) parser.parse(reader);
        } catch (IOException | ParseException e) {
            System.err.println("Error loading users: " + e.getMessage());
            return new JSONObject();
        }
    }

    private void saveUsers(JSONObject users) {
        try (FileWriter writer = new FileWriter(USERS_FILE)) {
            writer.write(users.toJSONString());
        } catch (IOException e) {
            System.err.println("Error saving users: " + e.getMessage());
        }
    }

    private static class User {
        private String username;
        private String password;
        private int privilege;

        public User(String username, String password, int privilege) {
            this.username = username;
            this.password = password;
            this.privilege = privilege;
        }

        public String getUsername() {
            return username;
        }

        public String getPassword() {
            return password;
        }

        public int getPrivilege() {
            return privilege;
        }
    }
}