import random, string, os, glob
import customtkinter
import tkinter as tk
from tkinter import filedialog
from cryptography.fernet import Fernet

login_path = ".credentials"
key_file = glob.glob(os.path.join(".credentials/", "*.key"))
pswd_file = glob.glob(os.path.join(".credentials/", "*.pswd"))

if key_file:
    key_file = key_file[0]
    with open(key_file, "rb") as f:
        key = f.read()
else:
    print("archivo no existe, se crea una nueva key")
    key = Fernet.generate_key()
    with open(f"{login_path}/{key.decode()[:16][::-1]}.key", "wb") as f:
        f.write(key)

fernet = Fernet(key)

if pswd_file:
    pswd_file = pswd_file[0]
    with open(pswd_file, "rb") as f:
        pswd = f.read()
else:
    print("archivo no existe, se crea una nueva password")
    pswd = input("contraseña >> ")
    pswd = fernet.encrypt(pswd.encode())
    with open(f"{login_path}/{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))}.pswd", "wb") as f:
        f.write(pswd)
