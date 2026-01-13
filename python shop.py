import customtkinter as ctk
import json
import os
import csv
from tkinter import messagebox, scrolledtext
from datetime import datetime

# Professional Theme
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class LaikaPetMartERP(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LAIKA PET MART - MASTER ADMIN ERP")
        self.geometry("1350x850")
        
        # Database setup
        self.db_folder = "Database"
        if not os.path.exists(self.db_folder): os.makedirs(self.db_folder)
        
        self.inv_file = os.path.join(self.db_folder, "inventory.json")
        self.sales_file = os.path.join(self.db_folder, "sales.json")
        self.users_file = os.path.join(self.db_folder, "users.json")
        self.ledger_file = os.path.join(self.db_folder, "ledger.json")
        self.exp_file = os.path.join(self.db_folder, "expenses.json")
        
        self.load_all_data()
        self.current_user = "admin" 
        self.setup_main_ui()

    def load_all_data(self):
        def loader(file, default):
            if os.path.exists(file):
                with open(file, "r") as f: return json.load(f)
            return default
        self.inventory = loader(self.inv_file, {})
        self.sales_history = loader(self.sales_file, [])
        self.ledger = loader(self.ledger_file, {"to_collect": [], "to_pay": []})
        self.expenses = loader(self.exp_file, [])
        self.users_db = loader(self.users_file, {
            "admin": {"password": "123", "name": "Ayush Saxena", "role": "Admin", 
                      "access": ["Dashboard", "Billing", "Stock", "Ledger", "Expenses", "Reports", "Settings"]}
        })

    def save_all(self):
        with open(self.inv_file, "w") as f: json.dump(self.inventory, f)
        with open(self.sales_file, "w") as f: json.dump(self.sales_history, f)
        with open(self.users_file, "w") as f: json.dump(self.users_db, f)
        with open(self.ledger_file, "w") as f: json.dump(self.ledger, f)
        with open(self.exp_file, "w") as f: json.dump(self.expenses, f)

    def setup_main_ui(self):
        for w in self.winfo_children(): w.destroy()
        # Header with NEW NAME
        header = ctk.CTkFrame(self, height=80, fg_color="#1a237e", corner_radius=0)
        header.pack(side="top", fill="x")
        u_name = self.users_db[self.current_user]["name"]
        ctk.CTkLabel(header, text=f"Welcome, {u_name} | LAIKA PET MART", text_color="white", font=("Helvetica", 20, "bold")).pack(side="left", padx=30)
        
        # Sidebar
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#f0f2f5")
        sidebar.pack(side="left", fill="y")
        
        menu = [("📊 Dashboard", self.show_dashboard, "#e3f2fd"),
                ("🧾 Billing", self.show_billing, "#fff3e0"),
                ("📦 Stock Entry", self.show_stock, "#f1f8e9"),
                ("💸 Udhaar Tracker", self.show_ledger, "#fce4ec"),
                ("💰 Expense Manager", self.show_expenses, "#ffebee"),
                ("📈 Excel Reports", self.show_reports, "#f3e5f5"),
                ("⚙️ Master Settings", self.show_settings, "#eceff1")]
        
        for t, c, clr in menu:
            ctk.CTkButton(sidebar, text=t, fg_color="transparent", text_color="black", anchor="w", height=60, font=("Helvetica", 15, "bold"), hover_color=clr, command=c).pack(pady=5, fill="x", padx=15)

        self.main = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=30)
        self.main.pack(side="right", fill="both", expand=True, padx=25, pady=25)
        self.show_dashboard()

    # --- 1. DASHBOARD WITH 4 CARDS ---
    def show_dashboard(self):
        for w in self.main.winfo_children(): w.destroy()
        t_sale = sum(s['total'] for s in self.sales_history)
        t_gross_profit = sum(s['profit'] for s in self.sales_history)
        t_pur = sum(v['p_price'] * v['qty'] for v in self.inventory.values())
        t_exp = sum(e['amount'] for e in self.expenses)
        net_profit = t_gross_profit - t_exp

        ctk.CTkLabel(self.main, text="LAIKA PET MART - FINANCIAL DASHBOARD", font=("Helvetica", 32, "bold"), text_color="#1a237e").pack(pady=30)
        grid = ctk.CTkFrame(self.main, fg_color="transparent")
        grid.pack(pady=10, fill="both", expand=True)

        self.create_card(grid, "TOTAL SALES", f"Rs. {t_sale:,}", "#1976d2").grid(row=0, column=0, padx=15, pady=15)
        self.create_card(grid, "TOTAL PURCHASE", f"Rs. {t_pur:,}", "#7b1fa2").grid(row=0, column=1, padx=15, pady=15)
        self.create_card(grid, "GROSS PROFIT", f"Rs. {t_gross_profit:,}", "#388e3c").grid(row=1, column=0, padx=15, pady=15)
        
        n_clr = "#2e7d32" if net_profit >= 0 else "#c62828"
        self.create_card(grid, "NET PROFIT", f"Rs. {net_profit:,}", n_clr).grid(row=1, column=1, padx=15, pady=15)
        grid.grid_columnconfigure((0,1), weight=1)

    def create_card(self, m, t, v, c):
        f = ctk.CTkFrame(m, fg_color=c, corner_radius=35, height=180)
        ctk.CTkLabel(f, text=t, text_color="white", font=("Arial", 16, "bold")).pack(pady=(40,0))
        ctk.CTkLabel(f, text=v, text_color="white", font=("Arial", 38, "bold")).pack(pady=20)
        f.grid_propagate(False); return f

    # --- 2. BILLING WITH RATE ---
    def show_billing(self):
        for w in self.main.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main, text="BILLING TERMINAL", font=("Helvetica", 28, "bold")).pack(pady=20)
        box = ctk.CTkFrame(self.main, corner_radius=20, border_width=1); box.pack(pady=20, padx=40, fill="x")
        self.bn = ctk.CTkEntry(box, placeholder_text="Product Name", width=250, height=45); self.bn.pack(side="left", padx=10, pady=30)
        self.bq = ctk.CTkEntry(box, placeholder_text="Qty", width=100, height=45); self.bq.pack(side="left", padx=10)
        self.br = ctk.CTkEntry(box, placeholder_text="Rate", width=120, height=45); self.br.pack(side="left", padx=10)
        ctk.CTkButton(box, text="PRINT BILL", fg_color="#2e7d32", height=45, command=self.do_sale).pack(side="left", padx=15)

    def do_sale(self):
        n, q_s, r_s = self.bn.get(), self.bq.get(), self.br.get()
        if n in self.inventory and q_s.isdigit() and r_s.replace('.','',1).isdigit():
            q, r = int(q_s), float(r_s); item = self.inventory[n]
            if item['qty'] >= q:
                t, p = r * q, (r - item['p_price']) * q
                self.inventory[n]['qty'] -= q
                self.sales_history.append({"date": datetime.now().strftime("%H:%M"), "item": n, "total": t, "profit": p})
                self.save_all(); self.show_billing()
                messagebox.showinfo("Billed", f"Rs. {t} Billed Successfully!")

    # --- 3. UDHAAR TRACKER (FIXED LIST) ---
    def show_ledger(self):
        for w in self.main.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main, text="UDHAAR TRACKER", font=("Helvetica", 28, "bold"), text_color="#1a237e").pack(pady=20)
        f = ctk.CTkFrame(self.main, corner_radius=15, fg_color="#f8f9fa"); f.pack(pady=10, fill="x", padx=30)
        self.pn = ctk.CTkEntry(f, placeholder_text="Party Name", width=250); self.pn.pack(side="left", padx=15, pady=25)
        self.pa = ctk.CTkEntry(f, placeholder_text="Amount", width=120); self.pa.pack(side="left", padx=10)
        self.pt = ctk.CTkComboBox(f, values=["Udhaar (Leva Hai)", "Payment (Dena Hai)"], width=180); self.pt.pack(side="left", padx=10)
        ctk.CTkButton(f, text="SAVE", fg_color="#1a237e", command=self.save_ledger).pack(side="left", padx=15)
        self.ltxt = scrolledtext.ScrolledText(self.main, width=110, height=20, font=("Consolas", 13)); self.ltxt.pack(pady=20, padx=30)
        self.refresh_ledger()

    def save_ledger(self):
        n, a, t = self.pn.get(), self.pa.get(), self.pt.get()
        if n and a.isdigit():
            e = {"name": n, "amount": int(a), "date": datetime.now().strftime("%d-%m-%Y")}
            if "Leva" in t: self.ledger["to_collect"].append(e)
            else: self.ledger["to_pay"].append(e)
            self.save_all(); self.refresh_ledger()

    def refresh_ledger(self):
        self.ltxt.delete("1.0", "end")
        self.ltxt.insert("end", "🔴 UDHAAR (LEVA HAI):\n" + "="*30 + "\n")
        for i in self.ledger["to_collect"]: self.ltxt.insert("end", f"{i['date']} | {i['name']:<20} | Rs. {i['amount']}\n")
        self.ltxt.insert("end", "\n🔵 PAYMENTS (DENA HAI):\n" + "="*30 + "\n")
        for i in self.ledger["to_pay"]: self.ltxt.insert("end", f"{i['date']} | {i['name']:<20} | Rs. {i['amount']}\n")

    # --- 4. EXPENSE WITH DROPDOWN ---
    def show_expenses(self):
        for w in self.main.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main, text="EXPENSE MANAGER", font=("Helvetica", 28, "bold"), text_color="#c62828").pack(pady=20)
        f = ctk.CTkFrame(self.main, corner_radius=15, fg_color="#f8f9fa"); f.pack(pady=10, fill="x", padx=30)
        self.ex_n = ctk.CTkEntry(f, placeholder_text="Name", width=200); self.ex_n.pack(side="left", padx=10, pady=25)
        self.ex_a = ctk.CTkEntry(f, placeholder_text="Amt", width=120); self.ex_a.pack(side="left", padx=10)
        self.ex_c = ctk.CTkComboBox(f, values=["Salary", "Rent", "Electricity", "Tea/Nashta", "Miscellaneous"], width=180)
        self.ex_c.pack(side="left", padx=10)
        ctk.CTkButton(f, text="SAVE", fg_color="#c62828", command=self.save_ex).pack(side="left", padx=10)
        self.extxt = scrolledtext.ScrolledText(self.main, width=110, height=18); self.extxt.pack(pady=20)
        for e in reversed(self.expenses): self.extxt.insert("end", f"{e['date']} | {e['name']} ({e['cat']}) | Rs. {e['amount']}\n")

    def save_ex(self):
        n, a, c = self.ex_n.get(), self.ex_a.get(), self.ex_c.get()
        if n and a.isdigit():
            self.expenses.append({"date": datetime.now().strftime("%d-%m"), "name": n, "cat": c, "amount": int(a)})
            self.save_all(); self.show_expenses()

    # --- 5. MASTER SETTINGS (ADMIN PROFILE FIXED) ---
    def show_settings(self):
        for w in self.main.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main, text="MASTER CONTROL PANEL", font=("Helvetica", 28, "bold")).pack(pady=20)
        tab = ctk.CTkTabview(self.main, width=950, height=550); tab.pack(pady=10)
        t_staff = tab.add("Staff & IDs"); t_profile = tab.add("Admin Profile")
        
        # Admin Profile Tab
        ctk.CTkLabel(t_profile, text="Update Admin Profile", font=("Arial", 16, "bold")).pack(pady=15)
        self.adm_n = ctk.CTkEntry(t_profile, placeholder_text="Admin Name", width=350); self.adm_n.pack(pady=10)
        self.adm_p = ctk.CTkEntry(t_profile, placeholder_text="New Password", width=350, show="*"); self.adm_p.pack(pady=10)
        ctk.CTkButton(t_profile, text="UPDATE ADMIN", command=self.upd_adm).pack(pady=20)
        
        # Staff Tab
        self.sid = ctk.CTkEntry(t_staff, placeholder_text="Staff ID", width=350); self.sid.pack(pady=10)
        self.spw = ctk.CTkEntry(t_staff, placeholder_text="Password", width=350); self.spw.pack(pady=10)
        ctk.CTkButton(t_staff, text="SAVE STAFF", command=self.add_staff).pack(pady=20)

    def upd_adm(self):
        n, p = self.adm_n.get(), self.adm_p.get()
        if n: self.users_db["admin"]["name"] = n
        if p: self.users_db["admin"]["password"] = p
        self.save_all(); self.setup_main_ui(); messagebox.showinfo("OK", "Profile Updated!")

    def add_staff(self):
        sid, spw = self.sid.get(), self.spw.get()
        if sid and spw:
            self.users_db[sid] = {"password": spw, "name": sid, "role": "Staff", "access": ["Dashboard", "Billing"]}
            self.save_all(); messagebox.showinfo("OK", "ID Created!")

    def show_stock(self):
        for w in self.main.winfo_children(): w.destroy()
        f = ctk.CTkFrame(self.main); f.pack(pady=10, fill="x", padx=25)
        self.ni = ctk.CTkEntry(f, placeholder_text="Item Name"); self.ni.pack(side="left", padx=5, pady=20)
        self.np = ctk.CTkEntry(f, placeholder_text="Buy Price"); self.np.pack(side="left", padx=5)
        self.ns = ctk.CTkEntry(f, placeholder_text="Sell Price"); self.ns.pack(side="left", padx=5)
        self.nq = ctk.CTkEntry(f, placeholder_text="Qty"); self.nq.pack(side="left", padx=5)
        ctk.CTkButton(f, text="+ Add Stock", command=self.add_inv).pack(side="left", padx=5)
        self.itxt = scrolledtext.ScrolledText(self.main, width=110, height=25); self.itxt.pack(pady=10)
        for k, v in self.inventory.items(): self.itxt.insert("end", f"{k:<30} | Stock: {v['qty']:<8} | Price: {v['s_price']}\n")

    def add_inv(self):
        n, p, s, q = self.ni.get(), self.np.get(), self.ns.get(), self.nq.get()
        if n and p and s:
            self.inventory[n] = {"p_price": float(p), "s_price": float(s), "qty": int(q)}
            self.save_all(); self.show_stock()

    def show_reports(self):
        for w in self.main.winfo_children(): w.destroy()
        ctk.CTkButton(self.main, text="EXPORT TO EXCEL (.CSV)", height=60, width=300, command=self.export).pack(pady=100)

    def export(self):
        if not self.sales_history: return
        fname = "Laika_Pet_Mart_Report.csv"
        with open(fname, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.sales_history[0].keys()); w.writeheader(); w.writerows(self.sales_history)
        messagebox.showinfo("OK", "Report Saved!")

if __name__ == "__main__":
    app = LaikaPetMartERP(); app.mainloop()