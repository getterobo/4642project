import tkinter as tk
from tkinter import messagebox
import os

# Create the main application window
root = tk.Tk()
root.title("Control Interface")
root.geometry("200x200")


#####################################################################
def view_ord():
    os.system('curl -X GET http://127.0.0.1:8080/simpleswitch/ord_list')


def ord_cmd():
    ord_list_window = tk.Tk()
    ord_list_window.title("ord list control")
    ord_list_window.geometry("200x200")
    ord_list_view_button = tk.Button(ord_list_window, text="view", command=view_ord)
    ord_list_view_button.pack(pady=0)


ord_list = tk.Button(root, text="ordinary list", command=ord_cmd)
ord_list.pack(pady=0)


#####################################################################
def view_high():
    comm = 'curl -X GET http://127.0.0.1:8080/simpleswitch/high_list/0000000000000001'
    os.system(comm)
    # print(comm)


def run_mod_high(val):
    h_id = f'10.0.0.{val}'
    comm1 = 'curl -X POST -d '
    comm2 = "\'{\"addr\":\"" + h_id + "\"}\' "
    comm3 = "http://127.0.0.1:8080/simpleswitch/high_list/0000000000000001"
    comm = comm1 + comm2 + comm3
    os.system(comm)
    # print(comm)


def choose_host_high():
    choose_h_win = tk.Tk()
    choose_h_win.title("Choose a host")
    choose_h_win.geometry("200x200")

    for i in range(1, 5 + 1):
        butt = tk.Button(choose_h_win, text=f"Host {i}", command=lambda i=i: run_mod_high(i))
        butt.pack(pady=0)


def high_cmd():
    high_list_window = tk.Tk()
    high_list_window.title("high list control")
    high_list_window.geometry("200x200")

    high_list_view_button = tk.Button(high_list_window, text="view", command=view_high)
    high_list_view_button.pack(pady=0)

    high_list_mod_button = tk.Button(high_list_window, text="mod", command=choose_host_high)
    high_list_mod_button.pack(pady=0)


high_list = tk.Button(root, text="high list", command=high_cmd)
high_list.pack(pady=0)


#####################################################################
def view_ban():
    comm = 'curl -X GET http://127.0.0.1:8080/simpleswitch/ban_list/0000000000000001'
    os.system(comm)


def lift_ban(val):
    h_id = f'10.0.0.{val}'
    comm1 = 'curl -X DELETE -d '
    comm2 = "\'{\"addr\":\"" + h_id + "\"}\' "
    comm3 = "http://127.0.0.1:8080/simpleswitch/ban_list/0000000000000001"
    comm = comm1 + comm2 + comm3
    os.system(comm)
    # print(comm)


def choose_host_ban():
    choose_h_win = tk.Tk()
    choose_h_win.title("Choose a host")
    choose_h_win.geometry("200x200")

    for i in range(1, 5 + 1):
        butt = tk.Button(choose_h_win, text=f"Host {i}", command=lambda i=i: lift_ban(i))
        butt.pack(pady=0)


def ban_cmd():
    ban_list_window = tk.Tk()
    ban_list_window.title("ban list control")
    ban_list_window.geometry("200x200")

    ban_list_view_button = tk.Button(ban_list_window, text="view", command=view_ban)
    ban_list_view_button.pack(pady=0)
    ban_list_mod_button = tk.Button(ban_list_window, text="lift ban", command=choose_host_ban)
    ban_list_mod_button.pack(pady=0)


ban_list = tk.Button(root, text="ban list", command=ban_cmd)
ban_list.pack(pady=0)


#####################################################################
def view_data_usage():
    comm = "curl -X GET http://127.0.0.1:8080/simpleswitch/data_usage/0000000000000001"
    # print(comm)
    os.system(comm)


def data_usage_cmd():
    data_window = tk.Tk()
    data_window.title("data usage control")
    data_window.geometry("200x200")

    data_usage_view_button = tk.Button(data_window, text="view", command=view_data_usage)
    data_usage_view_button.pack(pady=0)


data_usage = tk.Button(root, text="data usage", command=data_usage_cmd)
data_usage.pack(pady=0)


#####################################################################
def clear_window():
    os.system("clear")


_clear = tk.Button(root, text="clear terminal", command=clear_window)
_clear.pack(pady=20)
#####################################################################
# Run the application
root.mainloop()