"""
Upgraded College Canteen Token System
- Brown-Beige themed UI
- Cart window with editable quantities and remove option
- Staff/Admin panel for token status updates (Pending -> Ready -> Collected)
- Custom popup windows for success/error/info
- Menu category "Beverages" merged into "Menu"
- SQLite database backend
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, simpledialog
from datetime import datetime
import hashlib
import random
import sys

# ---------------------------
# Configuration / Theme
# ---------------------------
DB_NAME = "college_canteen_upgraded.db"

THEME = {
    'bg': '#efe6da',         # page background (beige)
    'card': 'pink',       # card/panel background (cream)
    'accent': '#c07a3f',     # warm brown accent
    'primary': '#5b3a29',    # dark brown text
    'muted': '#7b6b61',      # muted text
    'success': '#2d8f6f',
    'danger': '#c0392b'
}

# ---------------------------
# Database Manager
# ---------------------------
class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.insert_sample_data()

    def create_tables(self):
        # Students Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                department TEXT,
                balance REAL DEFAULT 0,
                password TEXT NOT NULL,
                registration_date TEXT
            )
        ''')
        # Menu Items Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT,
                price REAL NOT NULL,
                description TEXT,
                available INTEGER DEFAULT 1
            )
        ''')
        # Orders Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                order_date TEXT,
                total_amount REAL,
                status TEXT,
                token_number INTEGER,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        # Order Items
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                item_id INTEGER,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
            )
        ''')
        # Admin Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT
            )
        ''')
        self.conn.commit()

    def insert_sample_data(self):
        # Insert Admin
        self.cursor.execute("SELECT * FROM admin WHERE username='admin'")
        if not self.cursor.fetchone():
            admin_pass = self.hash_password("admin123")
            self.cursor.execute("INSERT INTO admin VALUES (?, ?, ?)",
                                ("admin", admin_pass, "Administrator"))

        # Insert Menu Items: note beverages category will be merged into "Menu"
        self.cursor.execute("SELECT COUNT(*) FROM menu_items")
        if self.cursor.fetchone()[0] == 0:
            menu = [
                ("Idli", "Breakfast", 30.0, "Soft steamed rice cakes (3 pcs)", 1),
                ("Dosa", "Breakfast", 40.0, "Crispy rice crepe with chutney", 1),
                ("Vada", "Breakfast", 25.0, "Fried lentil donuts (2 pcs)", 1),
                ("Poha", "Breakfast", 30.0, "Flattened rice with spices", 1),
                ("Upma", "Breakfast", 35.0, "Semolina porridge", 1),

                ("Rice Plate", "Main Course", 50.0, "Rice with dal and curry", 1),
                ("Chapati Set", "Main Course", 45.0, "3 chapatis with curry", 1),
                ("Pulao", "Main Course", 60.0, "Vegetable fried rice", 1),
                ("Biryani", "Main Course", 80.0, "Spiced rice with vegetables", 1),
                ("Curd Rice", "Main Course", 40.0, "Rice with yogurt", 1),

                ("Samosa", "Snacks", 15.0, "Crispy pastry with filling (1 pc)", 1),
                ("Vadapav", "Snacks", 20.0, "Mumbai street food", 1),
                ("Sandwich", "Snacks", 35.0, "Grilled vegetable sandwich", 1),
                ("Burger", "Snacks", 50.0, "Veg burger with fries", 1),
                ("Pakoda", "Snacks", 25.0, "Fried fritters", 1),

                # Original 'Beverages' entries — we will set category as "Menu" to remove beverage heading
                ("Tea", "Menu", 10.0, "Indian masala tea", 1),
                ("Coffee", "Menu", 15.0, "Hot filter coffee", 1),
                ("Cold Coffee", "Menu", 30.0, "Iced coffee shake", 1),
                ("Lassi", "Menu", 25.0, "Yogurt-based drink", 1),
                ("Juice", "Menu", 20.0, "Fresh fruit juice", 1),
                ("Soft Drink", "Menu", 20.0, "Chilled soda", 1),

                ("Ice Cream", "Desserts", 30.0, "Vanilla/Chocolate cup", 1),
                ("Gulab Jamun", "Desserts", 20.0, "Sweet milk balls (2 pcs)", 1),
                ("Jalebi", "Desserts", 25.0, "Crispy sweet pretzel", 1)
            ]
            self.cursor.executemany(
                "INSERT INTO menu_items (item_name, category, price, description, available) VALUES (?, ?, ?, ?, ?)",
                menu
            )
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    # student methods
    def register_student(self, student_id, name, email, phone, department, password, balance=0):
        try:
            hashed_pw = self.hash_password(password)
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (student_id, name, email, phone, department, balance, hashed_pw, reg_date)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_student(self, student_id, password):
        hashed_pw = self.hash_password(password)
        self.cursor.execute(
            "SELECT * FROM students WHERE student_id=? AND password=?",
            (student_id, hashed_pw)
        )
        return self.cursor.fetchone()

    def get_student_info(self, student_id):
        self.cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        return self.cursor.fetchone()

    def verify_admin(self, username, password):
        hashed_pw = self.hash_password(password)
        self.cursor.execute(
            "SELECT * FROM admin WHERE username=? AND password=?", 
            (username, hashed_pw)
        )
        return self.cursor.fetchone()

    def get_balance(self, student_id):
        self.cursor.execute("SELECT balance FROM students WHERE student_id=?", (student_id,))
        result = self.cursor.fetchone()
        return float(result[0]) if result else 0.0

    def add_balance(self, student_id, amount):
        self.cursor.execute(
            "UPDATE students SET balance = balance + ? WHERE student_id=?", 
            (amount, student_id)
        )
        self.conn.commit()

    def get_menu_by_category(self):
        # Load available items and group by category.
        # Note: beverages have been put in category 'Menu' already, so there's no 'Beverages' heading.
        self.cursor.execute("SELECT * FROM menu_items WHERE available=1 ORDER BY category, item_name")
        items = self.cursor.fetchall()
        categories = {}
        for item in items:
            cat = item[2] or "Menu"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        return categories

    def place_order(self, student_id, cart_items, total_amount):
        try:
            token_number = random.randint(100, 999)
            order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.cursor.execute(
                "INSERT INTO orders (student_id, order_date, total_amount, status, token_number) VALUES (?, ?, ?, ?, ?)",
                (student_id, order_date, total_amount, "Pending", token_number)
            )
            order_id = self.cursor.lastrowid

            for item in cart_items:
                self.cursor.execute(
                    "INSERT INTO order_items (order_id, item_id, quantity, price) VALUES (?, ?, ?, ?)",
                    (order_id, item['id'], item['quantity'], item['price'])
                )

            # Deduct balance
            self.cursor.execute(
                "UPDATE students SET balance = balance - ? WHERE student_id=?",
                (total_amount, student_id)
            )
            self.conn.commit()
            return token_number
        except Exception as e:
            self.conn.rollback()
            print("Order error:", e)
            return None

    def get_order_history(self, student_id, limit=50):
        self.cursor.execute('''
            SELECT o.order_id, o.order_date, o.total_amount, o.status, o.token_number
            FROM orders o
            WHERE o.student_id = ?
            ORDER BY o.order_date DESC
            LIMIT ?
        ''', (student_id, limit))
        return self.cursor.fetchall()

    def get_order_details(self, order_id):
        self.cursor.execute('''
            SELECT m.item_name, oi.quantity, oi.price, (oi.quantity * oi.price) as subtotal
            FROM order_items oi
            JOIN menu_items m ON oi.item_id = m.item_id
            WHERE oi.order_id = ?
        ''', (order_id,))
        return self.cursor.fetchall()

    def get_all_students(self):
        self.cursor.execute(
            "SELECT student_id, name, email, department, balance, registration_date FROM students"
        )
        return self.cursor.fetchall()

    def get_all_orders(self, limit=100):
        self.cursor.execute('''
            SELECT o.order_id, s.name, s.student_id, o.order_date, o.total_amount, o.status, o.token_number
            FROM orders o
            JOIN students s ON o.student_id = s.student_id
            ORDER BY o.order_date DESC
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()

    def update_order_status(self, order_id, new_status):
        self.cursor.execute(
            "UPDATE orders SET status=? WHERE order_id=?", (new_status, order_id)
        )
        self.conn.commit()

    def get_revenue_stats(self):
        self.cursor.execute("SELECT SUM(total_amount) FROM orders")
        total_revenue = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT COUNT(*) FROM students")
        total_students = self.cursor.fetchone()[0] or 0

        return {'revenue': total_revenue, 'orders': total_orders, 'students': total_students}

    def close(self):
        self.conn.close()

# ---------------------------
# Helper UI Components
# ---------------------------
class StyledPopup(tk.Toplevel):
    """Custom simple styled popup to replace default messagebox visuals."""
    def __init__(self, master, title, message, type="info"):
        super().__init__(master)
        self.title(title)
        self.configure(bg=THEME['bg'])
        self.resizable(False, False)
        self.grab_set()
        self.transient(master)

        frame = tk.Frame(self, bg=THEME['card'], padx=18, pady=12)
        frame.pack(padx=12, pady=12)

        # Icon area
        icon = "ℹ️"
        fg = THEME['primary']
        if type == "success":
            icon = "✅"
            fg = THEME['success']
        elif type == "error":
            icon = "❌"
            fg = THEME['danger']
        elif type == "warn":
            icon = "⚠️"
            fg = THEME['accent']

        icon_lbl = tk.Label(frame, text=icon, font=("Segoe UI Emoji", 20), bg=THEME['card'])
        icon_lbl.grid(row=0, column=0, rowspan=2, padx=(0,10))

        msg_lbl = tk.Label(frame, text=message, font=("Arial", 11), bg=THEME['card'], fg=THEME['primary'], justify="left", wraplength=380)
        msg_lbl.grid(row=0, column=1, sticky="w")

        ok_btn = tk.Button(frame, text="OK", bg=THEME['accent'], fg="white", relief="flat", width=10, command=self.destroy)
        ok_btn.grid(row=1, column=1, pady=(10,0), sticky="e")

# ---------------------------
# Main Application (Tkinter)
# ---------------------------
class CanteenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("College Canteen Token System")
        self.root.geometry("1150x720")
        self.root.configure(bg=THEME['bg'])

        self.db = DatabaseManager()
        self.current_user = None  # student tuple when logged in
        self.cart = []  # list of dicts: {id, name, price, quantity}

        self.setup_login_screen()

    # ---------- Utilities ----------
    def clear_window(self):
        for w in self.root.winfo_children():
            w.destroy()

    def center_window(self, win, w=420, h=200):
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    # ---------- Login / Registration ----------
    def setup_login_screen(self):
        self.clear_window()

        frame = tk.Frame(self.root, bg=THEME['card'], padx=24, pady=24)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(frame, text="College Canteen", font=("Georgia", 28, "bold"), bg=THEME['card'], fg=THEME['primary'])
        title.pack(pady=(0,10))

        sub = tk.Label(frame, text="Token Management System", font=("Arial", 12), bg=THEME['card'], fg=THEME['muted'])
        sub.pack(pady=(0,12))

        # Login fields
        login_frame = tk.Frame(frame, bg=THEME['card'])
        login_frame.pack(pady=6)

        tk.Label(login_frame, text="Student ID / Admin Username", bg=THEME['card'], fg=THEME['primary']).grid(row=0, column=0, sticky="w")
        self.login_id_entry = tk.Entry(login_frame, width=28, bd=3, relief="flat")
        self.login_id_entry.grid(row=1, column=0, pady=(3,8))

        tk.Label(login_frame, text="Password", bg=THEME['card'], fg=THEME['primary']).grid(row=2, column=0, sticky="w")
        self.login_pass_entry = tk.Entry(login_frame, width=28, bd=3, relief="flat", show="*")
        self.login_pass_entry.grid(row=3, column=0, pady=(3,8))

        btn_frame = tk.Frame(frame, bg=THEME['card'])
        btn_frame.pack(pady=6)

        stu_btn = tk.Button(btn_frame, text="Student Login", bg=THEME['accent'], fg="white", relief="flat",
                            width=18, command=self.student_login)
        stu_btn.pack(side="left", padx=6)

        adm_btn = tk.Button(btn_frame, text="Admin Login", bg=THEME['primary'], fg="white", relief="flat",
                            width=18, command=self.admin_login)
        adm_btn.pack(side="left", padx=6)

        reg_txt = tk.Label(frame, text="New student? Register below", bg=THEME['card'], fg=THEME['muted'])
        reg_txt.pack(pady=(12,4))

        reg_btn = tk.Button(frame, text="Register as Student", bg="#f4d8c1", fg=THEME['primary'], relief="flat", width=20, command=self.show_registration)
        reg_btn.pack()

    def show_registration(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg=THEME['card'], padx=20, pady=16)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Student Registration", font=("Georgia", 18, "bold"), bg=THEME['card'], fg=THEME['primary']).pack(pady=(0,12))

        fields = [
            ("Student ID", "id"),
            ("Full Name", "name"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Department", "department"),
            ("Password", "password"),
            ("Confirm Password", "confirm")
        ]
        self.reg_vars = {}
        form = tk.Frame(frame, bg=THEME['card'])
        form.pack()
        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, bg=THEME['card'], fg=THEME['primary']).grid(row=i, column=0, sticky="w", pady=6)
            ent = tk.Entry(form, width=36, bd=2, relief="flat", show="*" if "pass" in key else "")
            ent.grid(row=i, column=1, padx=12, pady=6)
            self.reg_vars[key] = ent

        btn_frame = tk.Frame(frame, bg=THEME['card'])
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Register", bg=THEME['accent'], fg="white", relief="flat", width=14, command=self.register_student).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Back", bg="#d7c6b8", fg=THEME['primary'], relief="flat", width=14, command=self.setup_login_screen).pack(side="left", padx=6)

    def register_student(self):
        data = {k: v.get().strip() for k, v in self.reg_vars.items()}
        if not all([data['id'], data['name'], data['email'], data['phone'], data['department'], data['password']]):
            StyledPopup(self.root, "Error", "All fields are required.", type="error")
            return
        if data['password'] != data['confirm']:
            StyledPopup(self.root, "Error", "Passwords do not match.", type="error")
            return
        if len(data['password']) < 6:
            StyledPopup(self.root, "Error", "Password must be at least 6 characters.", type="error")
            return
        success = self.db.register_student(data['id'], data['name'], data['email'], data['phone'], data['department'], data['password'], 0)
        if success:
            StyledPopup(self.root, "Success", f"Registration successful!\nStudent ID: {data['id']}", type="success")
            self.setup_login_screen()
        else:
            StyledPopup(self.root, "Error", "Student ID already exists.", type="error")

    def student_login(self):
        sid = self.login_id_entry.get().strip()
        pwd = self.login_pass_entry.get()
        if not sid or not pwd:
            StyledPopup(self.root, "Error", "Please enter both Student ID and Password.", type="error")
            return
        user = self.db.verify_student(sid, pwd)
        if user:
            self.current_user = user
            self.show_student_dashboard()
        else:
            StyledPopup(self.root, "Error", "Invalid Student ID or Password.", type="error")

    def admin_login(self):
        username = self.login_id_entry.get().strip()
        password = self.login_pass_entry.get()
        if not username or not password:
            StyledPopup(self.root, "Error", "Please enter both Username and Password.", type="error")
            return
        admin = self.db.verify_admin(username, password)
        if admin:
            self.show_admin_dashboard()
        else:
            StyledPopup(self.root, "Error", "Invalid Admin Credentials.", type="error")

    # ---------- Student Dashboard ----------
    def show_student_dashboard(self):
        self.clear_window()
        # Refresh user
        self.current_user = self.db.get_student_info(self.current_user[0])

        # Top Nav
        nav = tk.Frame(self.root, bg=THEME['primary'], height=80)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        left = tk.Frame(nav, bg=THEME['primary'])
        left.pack(side="left", padx=20)
        tk.Label(left, text=f"👋 Welcome, {self.current_user[1]}", bg=THEME['primary'], fg="white", font=("Arial", 16, "bold")).pack(anchor="w")
        tk.Label(left, text=f"ID: {self.current_user[0]}  |  {self.current_user[4]}", bg=THEME['primary'], fg="#f0d9c2", font=("Arial", 10)).pack(anchor="w")

        right = tk.Frame(nav, bg=THEME['primary'])
        right.pack(side="right", padx=20)
        bal = self.db.get_balance(self.current_user[0])
        bal_frame = tk.Frame(right, bg="#f7d9bf", padx=12, pady=6)
        bal_frame.pack(side="left", padx=6)
        tk.Label(bal_frame, text="💰 Balance", bg="#f7d9bf", fg=THEME['primary']).pack()
        self.balance_label = tk.Label(bal_frame, text=f"₹{bal:.2f}", bg="#f7d9bf", fg=THEME['primary'], font=("Arial", 14, "bold"))
        self.balance_label.pack()

        tk.Button(right, text="💵 Add Money", bg=THEME['accent'], fg="white", relief="flat", command=self.add_money).pack(side="left", padx=6)
        tk.Button(right, text="📜 Orders", bg="#8e6a52", fg="white", relief="flat", command=self.show_order_history).pack(side="left", padx=6)
        tk.Button(right, text="🚪 Logout", bg=THEME['primary'], fg="white", relief="flat", command=self.logout_to_login).pack(side="left", padx=6)

        # Body
        body = tk.Frame(self.root, bg=THEME['bg'])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Menu area (left)
        menu_area = tk.Frame(body, bg=THEME['card'], bd=1, relief="solid")
        menu_area.pack(side="left", fill="both", expand=True, padx=(0,10), pady=6)
        tk.Label(menu_area, text="🍽️ MENU", font=("Georgia", 20, "bold"), bg=THEME['card'], fg=THEME['primary']).pack(pady=12)

        # Scrollable canvas for menu
        canvas = tk.Canvas(menu_area, bg=THEME['card'], highlightthickness=0)
        scrollbar = tk.Scrollbar(menu_area, orient="vertical", command=canvas.yview)
        menu_frame = tk.Frame(canvas, bg=THEME['card'])
        menu_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=menu_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        categories = self.db.get_menu_by_category()
        # Create category headers and cards
        for category, items in categories.items():
            # Category header
            cat_label = tk.Label(menu_frame, text=f"🔸 {category}", font=("Arial", 13, "bold"), bg=THEME['card'], fg=THEME['accent'])
            cat_label.pack(fill="x", padx=12, pady=(8,5))
            for item in items:
                self.create_menu_card(menu_frame, item)

        # Cart area (right)
        cart_area = tk.Frame(body, bg=THEME['card'], width=360)
        cart_area.pack(side="right", fill="y", padx=(10,0), pady=6)
        cart_area.pack_propagate(False)
        tk.Label(cart_area, text="🛒 YOUR ORDER", font=("Georgia", 16, "bold"), bg=THEME['card'], fg=THEME['primary']).pack(pady=12)

        # Cart display (Treeview)
        self.cart_tree = ttk.Treeview(cart_area, columns=("Item","Qty","Price"), show="headings", height=12)
        self.cart_tree.heading("Item", text="Item")
        self.cart_tree.heading("Qty", text="Qty")
        self.cart_tree.heading("Price", text="Subtotal")
        self.cart_tree.column("Item", width=160)
        self.cart_tree.column("Qty", width=45, anchor="center")
        self.cart_tree.column("Price", width=80, anchor="e")
        self.cart_tree.pack(padx=12, pady=6, fill="both", expand=True)

        # Buttons under cart
        btns = tk.Frame(cart_area, bg=THEME['card'])
        btns.pack(pady=8)
        tk.Button(btns, text="➕ Add Item", bg="#f4d8c1", fg=THEME['primary'], relief="flat", command=self.open_add_item_from_menu).pack(side="left", padx=6)
        tk.Button(btns, text="🗑️ Remove Selected", bg="#e0b7a0", fg=THEME['primary'], relief="flat", command=self.remove_selected_cart).pack(side="left", padx=6)
        tk.Button(btns, text="✅ PLACE ORDER", bg=THEME['accent'], fg="white", relief="flat", command=self.checkout).pack(side="left", padx=6)

        self.update_cart_ui()

    def create_menu_card(self, parent, item):
        # item tuple: (item_id, item_name, category, price, description, available)
        card = tk.Frame(parent, bg="white", bd=1, relief="solid")
        card.pack(fill="x", padx=12, pady=6)
        left = tk.Frame(card, bg="white")
        left.pack(side="left", padx=10, pady=8, fill="x", expand=True)
        tk.Label(left, text=item[1], font=("Arial", 12, "bold"), bg="white", fg=THEME['primary']).pack(anchor="w")
        tk.Label(left, text=item[4], font=("Arial", 9), bg="white", fg=THEME['muted']).pack(anchor="w", pady=(2,0))

        right = tk.Frame(card, bg="white")
        right.pack(side="right", padx=10, pady=8)
        tk.Label(right, text=f"₹{item[3]:.0f}", font=("Arial", 12, "bold"), bg="white", fg=THEME['success']).pack()
        tk.Button(right, text="+ Add", bg=THEME['accent'], fg="white", relief="flat", command=lambda i=item: self.add_to_cart(i)).pack(pady=6)

    def add_to_cart(self, item):
        # item: DB row tuple
        found = False
        for ci in self.cart:
            if ci['id'] == item[0]:
                ci['quantity'] += 1
                found = True
                break
        if not found:
            self.cart.append({'id': item[0], 'name': item[1], 'price': float(item[3]), 'quantity': 1})
        self.update_cart_ui()

    # invoked by button in cart area to open menu (fast add)
    def open_add_item_from_menu(self):
        menu_win = tk.Toplevel(self.root)
        menu_win.title("Add Item")
        menu_win.configure(bg=THEME['bg'])
        menu_win.geometry("360x420")
        canvas = tk.Canvas(menu_win, bg=THEME['card'], highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=10)
        items = []
        categories = self.db.get_menu_by_category()
        for cat, its in categories.items():
            tk.Label(canvas, text=cat, font=("Arial", 12, "bold"), bg=THEME['card'], fg=THEME['accent']).pack(anchor="w", pady=6)
            for item in its:
                btn = tk.Button(canvas, text=f"{item[1]} - ₹{item[3]:.0f}", bg="white", relief="flat", command=lambda i=item, w=menu_win: (self.add_to_cart(i), w.destroy()))
                btn.pack(fill="x", pady=3)

    def update_cart_ui(self):
        # refresh tree
        for r in self.cart_tree.get_children():
            self.cart_tree.delete(r)
        total = 0
        for ci in self.cart:
            subtotal = ci['price'] * ci['quantity']
            total += subtotal
            self.cart_tree.insert("", "end", iid=str(ci['id']), values=(ci['name'], ci['quantity'], f"₹{subtotal:.0f}"))
        # footer total label
        if hasattr(self, 'total_label'):
            self.total_label.destroy()
        self.total_label = tk.Label(self.root, text=f"TOTAL: ₹{total:.2f}", bg=THEME['bg'], fg=THEME['primary'], font=("Arial", 14, "bold"))
        # place it at bottom-right area (pack/place trick)
        # remove old if exists
        try:
            self.total_label.place_forget()
        except:
            pass
        # place near cart area (approx coordinates)
        self.total_label.place(relx=0.82, rely=0.86)

        # Update balance label
        if self.current_user:
            bal = self.db.get_balance(self.current_user[0])
            self.balance_label.config(text=f"₹{bal:.2f}")

    def remove_selected_cart(self):
        sel = self.cart_tree.selection()
        if not sel:
            StyledPopup(self.root, "Info", "Select an item in cart to remove.", type="info")
            return
        for iid in sel:
            iid_int = int(iid)
            # find in cart
            for ci in self.cart:
                if ci['id'] == iid_int:
                    self.cart.remove(ci)
                    break
        self.update_cart_ui()

    def checkout(self):
        if not self.cart:
            StyledPopup(self.root, "Empty Cart", "Please add items to cart first!", type="warn")
            return
        total = sum(ci['price'] * ci['quantity'] for ci in self.cart)
        bal = self.db.get_balance(self.current_user[0])
        if bal < total:
            short = total - bal
            StyledPopup(self.root, "Insufficient Balance", f"Your balance is ₹{bal:.2f}\nOrder total is ₹{total:.2f}\nAdd ₹{short:.2f} to proceed.", type="error")
            return

        # Confirm dialog (simple)
        confirm = simpledialog.askstring("Confirm Order", f"Total: ₹{total:.2f}\nType YES to confirm:")
        if (not confirm) or confirm.strip().lower() != "yes":
            StyledPopup(self.root, "Cancelled", "Order not placed.", type="info")
            return

        # place order by mapping cart to DB format
        items_for_db = [{'id': ci['id'], 'quantity': ci['quantity'], 'price': ci['price']} for ci in self.cart]
        token = self.db.place_order(self.current_user[0], items_for_db, total)
        if token:
            StyledPopup(self.root, "Order Placed", f"✅ Order placed successfully!\nToken: {token}\nPlease collect your food when status is Ready.", type="success")
            self.cart = []
            # refresh student data & dashboard
            self.current_user = self.db.get_student_info(self.current_user[0])
            self.show_student_dashboard()
        else:
            StyledPopup(self.root, "Error", "Failed to place order. Try again.", type="error")

    def add_money(self):
        amount = simpledialog.askfloat("Add Money", "Enter amount to add (₹10 - ₹5000):", minvalue=10, maxvalue=5000)
        if amount is None:
            return
        self.db.add_balance(self.current_user[0], amount)
        StyledPopup(self.root, "Success", f"₹{amount:.2f} added to your wallet.", type="success")
        self.current_user = self.db.get_student_info(self.current_user[0])
        self.show_student_dashboard()

    def show_order_history(self):
        win = tk.Toplevel(self.root)
        win.title("Order History")
        win.geometry("900x500")
        win.configure(bg=THEME['bg'])
        tk.Label(win, text="📜 Order History", bg=THEME['bg'], fg=THEME['primary'], font=("Georgia", 16, "bold")).pack(pady=12)

        tree_frame = tk.Frame(win, bg=THEME['card'])
        tree_frame.pack(fill="both", expand=True, padx=12, pady=8)
        cols = ("Order ID", "Date", "Amount", "Status", "Token")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, side="left")
        scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        orders = self.db.get_order_history(self.current_user[0])
        if not orders:
            tree.insert("", "end", values=("", "No orders yet", "", "", ""))
        else:
            for order in orders:
                tree.insert("", "end", values=order)

        tk.Button(win, text="Close", bg=THEME['accent'], fg="white", relief="flat", command=win.destroy).pack(pady=10)

    def logout_to_login(self):
        self.current_user = None
        self.cart = []
        self.setup_login_screen()

    # ---------- Admin Dashboard ----------
    def show_admin_dashboard(self):
        self.clear_window()
        # Top Bar
        top = tk.Frame(self.root, bg=THEME['accent'], height=80)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="👨‍💼 ADMIN DASHBOARD", bg=THEME['accent'], fg="white", font=("Georgia", 20, "bold")).pack(side="left", padx=24)
        tk.Button(top, text="Logout", bg=THEME['primary'], fg="white", relief="flat", command=self.setup_login_screen).pack(side="right", padx=24)

        # Stats
        stats = self.db.get_revenue_stats()
        stats_frame = tk.Frame(self.root, bg=THEME['bg'])
        stats_frame.pack(fill="x", padx=20, pady=16)
        for label, value, color in [
            ("Total Revenue", f"₹{stats['revenue']:.2f}", THEME['success']),
            ("Total Orders", str(stats['orders']), THEME['accent']),
            ("Total Students", str(stats['students']), THEME['primary'])
        ]:
            card = tk.Frame(stats_frame, bg=color, padx=18, pady=12)
            card.pack(side="left", expand=True, fill="both", padx=10)
            tk.Label(card, text=label, bg=color, fg="white").pack()
            tk.Label(card, text=value, bg=color, fg="white", font=("Arial", 20, "bold")).pack()

        # Notebook for Students / Orders
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0,20))
        students_frame = tk.Frame(notebook, bg=THEME['card'])
        orders_frame = tk.Frame(notebook, bg=THEME['card'])
        notebook.add(students_frame, text="👥 Students")
        notebook.add(orders_frame, text="📦 Orders")

        # Students table
        self.populate_students_table(students_frame)
        # Orders table with ability to update status
        self.populate_orders_table(orders_frame)

    def populate_students_table(self, parent):
        tree_frame = tk.Frame(parent, bg=THEME['card'])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        cols = ("ID", "Name", "Email", "Department", "Balance", "Reg Date")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=140)
        tree.pack(fill="both", expand=True)

        students = self.db.get_all_students()
        for s in students:
            tree.insert("", "end", values=s)

    def populate_orders_table(self, parent):
        tree_frame = tk.Frame(parent, bg=THEME['card'])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        cols = ("Order ID", "Student", "ID", "Date", "Amount", "Status", "Token")
        self.orders_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        for c in cols:
            self.orders_tree.heading(c, text=c)
            self.orders_tree.column(c, width=120)
        self.orders_tree.pack(fill="both", expand=True, side="left")
        scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=self.orders_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.orders_tree.configure(yscrollcommand=scrollbar.set)

        self.load_orders_into_tree()

        # Buttons to update status
        btn_frame = tk.Frame(parent, bg=THEME['card'])
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Mark Ready", bg="#f4d8c1", fg=THEME['primary'], relief="flat", command=lambda: self.change_selected_order_status("Ready")).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Mark Collected", bg="#d7c6b8", fg=THEME['primary'], relief="flat", command=lambda: self.change_selected_order_status("Collected")).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Refresh", bg=THEME['accent'], fg="white", relief="flat", command=self.load_orders_into_tree).pack(side="left", padx=6)

    def load_orders_into_tree(self):
        for r in self.orders_tree.get_children():
            self.orders_tree.delete(r)
        orders = self.db.get_all_orders()
        for o in orders:
            self.orders_tree.insert("", "end", values=o)

    def change_selected_order_status(self, new_status):
        sel = self.orders_tree.selection()
        if not sel:
            StyledPopup(self.root, "Error", "Select an order to update.", type="error")
            return
        for iid in sel:
            vals = self.orders_tree.item(iid, "values")
            order_id = vals[0]
            self.db.update_order_status(order_id, new_status)
        StyledPopup(self.root, "Success", f"Order(s) status updated to {new_status}.", type="success")
        self.load_orders_into_tree()

# ---------------------------
# Run application
# ---------------------------
def main():
    root = tk.Tk()
    app = CanteenApp(root)
    root.mainloop()
    app.db.close()

if __name__ == "__main__":
    main()