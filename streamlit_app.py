import streamlit as st
import sqlite3
import datetime
import re

# --- Configuración de la base de datos ---
conn = sqlite3.connect('finanzasapp.db', check_same_thread=False)
c = conn.cursor()

# Crear tablas de usuarios y transacciones
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                balance REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                transaction_type TEXT,
                amount REAL,
                date TEXT,
                status TEXT)''')
conn.commit()

def register_user(username, password, initial_balance=1000):
    # Verificar si el usuario ya existe
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone() is not None:
        st.error("El nombre de usuario ya está en uso.") 
      return    
  # Verificar si los campos de usuario y contraseña no están en blanco
    if not username or not password:
        st.error("El nombre de usuario y la contraseña no pueden estar en blanco.")
        return
   # Verificar si los campos de usuario y contraseña no contienen caracteres especiales
    if not re.match("^[a-zA-Z0-9_]+$", username) or not re.match("^[a-zA-Z0-9_]+$", password):
        st.error("El nombre de usuario y la contraseña no pueden contener caracteres especiales.")
        return
    # Registrar el nuevo usuario
    c.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, initial_balance))
    conn.commit()
    st.success("Usuario registrado correctamente")


def login_user(username, password):
    # Verificar si el usuario y la contraseña son correctos
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def create_transaction(user_id, transaction_type, amount):
    # No valida si el usuario tiene saldo suficiente (fallo en la transacción de retiro)
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = c.fetchone()[0]
    # Permite retirar más de lo disponible (fallo)
    if transaction_type == "Retiro" and amount > balance:
        st.error("Saldo insuficiente para realizar esta transacción.")
        return
    # Registra la transacción
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_balance = balance - amount if transaction_type == "Retiro" else balance + amount
    c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    c.execute("INSERT INTO transactions (user_id, transaction_type, amount, date, status) VALUES (?, ?, ?, ?, ?)",
              (user_id, transaction_type, amount, date, "completada"))
    conn.commit()
    st.success(f"{transaction_type} de ${amount} realizada correctamente")

def get_transactions(user_id):
    c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
    return c.fetchall()

# --- Interfaz Streamlit ---
st.title("FinanzasApp - Gestión Financiera (Versión con fallos)")

menu = ["Inicio", "Registro", "Login", "Realizar Transacción", "Ver Transacciones", "Ver Balance", "Cerrar Sesión"]
choice = st.sidebar.selectbox("Menú", menu)

if choice == "Registro":
    st.subheader("Registro de Usuario")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type='password')
    initial_balance = st.number_input("Saldo inicial", min_value=1000, value=1000)
    if st.button("Registrar"):
        register_user(username, password, initial_balance)
        st.success("Usuario registrado correctamente")

elif choice == "Login":
    st.subheader("Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type='password')
    if st.button("Ingresar"):
        user = login_user(username, password)
        if user:
            st.session_state['user'] = user
            st.success(f"Bienvenido {user[1]}")
        else:
            st.error("Usuario o contraseña incorrectos")

elif choice == "Realizar Transacción":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión")
    else:
        st.subheader("Realizar Transacción")
        transaction_type = st.selectbox("Tipo de transacción", ["Depósito", "Retiro"])
        amount = st.number_input("Monto", min_value=0.01)
        if st.button("Realizar"):
            create_transaction(st.session_state['user'][0], transaction_type, amount)

elif choice == "Ver Transacciones":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión")
    else:
        st.subheader("Listado de Transacciones")
        transactions = get_transactions(st.session_state['user'][0])
        for transaction in transactions:
            st.write(f"ID: {transaction[0]} | Tipo: {transaction[2]} | Monto: ${transaction[3]} | Fecha: {transaction[4]} | Estado: {transaction[5]}")

elif choice == "Ver Balance":
    if 'user' not in st.session_state:
        st.warning("Debes iniciar sesión")
    else:
        st.subheader("Tu Balance")
        c.execute("SELECT balance FROM users WHERE id = ?", (st.session_state['user'][0],))
        balance = c.fetchone()[0]
        st.write(f"Tu balance actual es: ${balance}")

elif choice == "Cerrar Sesión":
    if 'user' in st.session_state:
        del st.session_state['user']
        st.success("Has cerrado sesión correctamente")
    else:
        st.warning("No has iniciado sesión")

else:
    st.write("Selecciona una opción en el menú de la izquierda.")
