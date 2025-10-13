import pyvisa as visa
import time
import numpy as np
import tkinter as tk
import os
import pandas as pd
from tkinter import ttk
import tkinter.font
from PIL import Image, ImageTk
from threading import *
from tkinter import messagebox as msgbox
from tkinter import filedialog, messagebox
import subprocess
import json

class tmp:
    
    def __init__(self, master):
        self.master = master
        self.event = Event()
        # master.title("IV Curve Measurement " + Version)
        # print("##############################################################")
        # print(f"Version : {Version}")
        # print("##############################################################")

        # self.df_config = pd.read_csv('Auto_Config.csv')
        # self.pin_list = self.df_config['Pin_Total'].to_list()
        # self.vinmin_list = self.df_config['Voltage_-'].to_list()
        # self.vinpl_list = self.df_config['Voltage_+'].to_list()
        # self.icomp_list = self.df_config['Current_Comp'].to_list()


        # self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        # self.plot_data = []
        self.json_path = 'json_overwriting.json'
        
        with open(self.json_path, 'r') as file:
            data = json.load(file)
            self.jmp_path = data["JMP_Path"]["Path"]
        
        print("JMP Path : ",self.jmp_path)
        self.create_widgets()

    def create_widgets(self):
        # Parameter Block
        parameter_frame = ttk.Frame(self.master)
        parameter_frame.grid(row=0, column=0, padx=10, pady=10)



        # Start Voltage Entry
        self.label_start_voltage = ttk.Label(parameter_frame, text="Path :")
        self.label_start_voltage.grid(row=0, column=0, padx=10, pady=10)
        self.entry_start_voltage = ttk.Entry(parameter_frame)
        self.entry_start_voltage.insert(0, self.jmp_path)
        self.entry_start_voltage.grid(row=0, column=1, padx=10, pady=10)

        # Button to Close Measurement
        self.button_update = ttk.Button(parameter_frame, text="JMP_Path", command=self.jmp_path_update)
        self.button_update.grid(row=1, column=0, padx=10, pady=10)

    def jmp_path_update(self):
        
        self.file_path = filedialog.askopenfilename(initialdir="C:/",filetypes=[("Executable files", "*.exe")])
        if self.file_path:
            self.jmp_path = self.file_path
            
            with open(self.json_path,'r') as file :
                data = json.load(file)

            
            data["JMP_Path"]["Path"] = self.jmp_path
                
            with open(self.json_path, 'w', encoding='utf-8') as file:
                json.dump(data,file,ensure_ascii=False,indent= 2)
            
            self.entry_start_voltage.delete(0, tk.END)
            self.entry_start_voltage.insert(0, self.jmp_path)



if __name__ == "__main__":
    root = tk.Tk()
    app = tmp(root)
    root.mainloop()
            