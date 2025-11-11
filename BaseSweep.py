
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
import subprocess
from tkinter import filedialog, messagebox
import json
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class BaseSweep(ttk.Frame):
    rm = visa.ResourceManager()

    def __init__(self, master, main_window, config):
        super().__init__(master)
        self.main_window = main_window
        self.config = config
        self.event = Event()
        self.json_path = 'Config.json'
        self.sourcetype = config["source_type"]

        self.df_config = pd.read_csv(config["config_file"])
        self.pin_list = self.df_config['Pin_Total'].to_list()
        
        if self.sourcetype == "Voltage source":
            self.vinmin_list = self.df_config['Voltage_-'].to_list()
            self.vinpl_list = self.df_config['Voltage_+'].to_list()
            self.icomp_list = self.df_config['Current_Comp'].to_list()
        else:
            self.cinmin_list = self.df_config['Current_-'].to_list()
            self.cinpl_list = self.df_config['Current_+'].to_list()
            self.vcomp_list = self.df_config['Voltage_Comp'].to_list()

        self.devlist = self.rm.list_resources()
        self.create_widgets()
        self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        self.plot_data = []
        self.create_widgets()

    def create_widgets(self):
        # --- 스크롤바를 위한 Canvas와 Frame 생성 ---
        # 1. Canvas 위젯을 생성하고 주 프레임에 배치합니다.
        canvas = tk.Canvas(self)
        canvas.grid(row=0, column=0, sticky="nsew")

        # 2. 수직 및 수평 스크롤바를 생성하고 Canvas에 연결합니다.
        v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # 3. 실제 위젯들이 담길 프레임(scrollable_frame)을 Canvas 내부에 생성합니다.
        scrollable_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # 4. scrollable_frame의 크기가 변경될 때마다 Canvas의 스크롤 영역을 업데이트하도록 바인딩합니다.
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # 5. 주 프레임의 grid 가중치를 설정하여 Canvas가 창 크기 변경에 따라 확장되도록 합니다.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- 마우스 휠 스크롤 바인딩 ---
        def _on_mouse_wheel(event):
            # Windows 및 macOS
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")

        # Canvas 자체와 Canvas 내부의 모든 위젯에 마우스 휠 이벤트 바인딩
        # bind_all을 사용하면 UI의 어느 곳에서든 휠 스크롤이 가능해집니다.
        self.bind_all("<MouseWheel>", _on_mouse_wheel) # Windows, macOS
        self.bind_all("<Button-4>", _on_mouse_wheel)   # Linux (scroll up)
        self.bind_all("<Button-5>", _on_mouse_wheel)   # Linux (scroll down)
        # --- 스크롤바 설정 끝 ---

        # Parameter Block
        parameter_frame = ttk.Frame(scrollable_frame) # 부모를 scrollable_frame으로 변경
        parameter_frame.grid(row=0, column=0, padx=10, pady=10)

        # Detail Block
        detail_frame = ttk.Frame(scrollable_frame) # 부모를 scrollable_frame으로 변경
        detail_frame.grid(row=1, column=0, padx=10, pady=10)
        header_font = tkinter.font.Font(family="Arial", weight="bold", size=15)
        header_font2 = tkinter.font.Font(family="Arial", weight="bold", size=11)

        # Frame for Image
        image_frame = ttk.Frame(scrollable_frame) # 부모를 scrollable_frame으로 변경
        image_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10)

        # Frame for Action button
        action_frame = ttk.Frame(scrollable_frame) # 부모를 scrollable_frame으로 변경
        action_frame.grid(row=2, column=0, columnspan=2)

        # Frame for IV plot
        plot_frame = ttk.Frame(scrollable_frame) # 부모를 scrollable_frame으로 변경
        plot_frame.grid(row=0, column=2, rowspan=2, padx=3, pady=3)

        # Label for plot
        self.plot_header = ttk.Label(plot_frame, text=self.config["plot_title"], font=header_font2)
        self.plot_header.grid(row=0, column=0, padx=10, pady=10)

        # Blank plot
        self.fig = plt.figure(figsize=(5, 5), dpi=130)
        self.ax = self.fig.add_axes([0.1, 0.1, 0.8, 0.8])
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=10)

        # Parameter Header
        self.header_parameter = ttk.Label(parameter_frame, text=self.config["param_header"], font=header_font)
        self.header_parameter.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Instrument Address Entry
        self.interface_type = ["GPIB", "Serial Interface"]
        self.combo_interface = ttk.Combobox(parameter_frame, values=self.interface_type, state="readonly")
        self.combo_interface.grid(row=1, column=0, padx=3, pady=10)
        self.combo_interface.bind("<<ComboboxSelected>>", self.on_interface_selected)

        self.entry_interface = ttk.Entry(parameter_frame)
        self.entry_interface.grid(row=1, column=1, padx=3, pady=10)

        # Interface Check Button
        self.button_interface_check = ttk.Button(parameter_frame, text="Interface Check", command=self.interface_check)
        self.button_interface_check.grid(row=1, column=2, padx=3, pady=10)

        # Start Entry
        self.label_start = ttk.Label(parameter_frame, text=self.config["start_label"])
        self.label_start.grid(row=2, column=0, padx=10, pady=10)
        self.entry_start = ttk.Entry(parameter_frame)
        self.entry_start.insert(0, self.config["start_default"])
        self.entry_start.grid(row=2, column=1, padx=10, pady=10)

        # Stop Entry
        self.label_stop = ttk.Label(parameter_frame, text=self.config["stop_label"])
        self.label_stop.grid(row=3, column=0, padx=10, pady=10)
        self.entry_stop = ttk.Entry(parameter_frame)
        self.entry_stop.insert(0, self.config["stop_default"])
        self.entry_stop.grid(row=3, column=1, padx=10, pady=10)

        # Step Entry
        self.label_step = ttk.Label(parameter_frame, text=self.config["step_label"])
        self.label_step.grid(row=4, column=0, padx=10, pady=10)
        self.entry_step = ttk.Entry(parameter_frame)
        self.entry_step.insert(0, "0.1")
        self.entry_step.grid(row=4, column=1, padx=10, pady=10)

        # Forward Compliance Entry
        self.label_compliacncef = ttk.Label(parameter_frame, text=self.config["fwd_limit_label"])
        self.label_compliacncef.grid(row=5, column=0, padx=10, pady=10)
        self.entry_compliacncef = ttk.Entry(parameter_frame)
        self.entry_compliacncef.insert(0, "1")
        self.entry_compliacncef.grid(row=5, column=1, padx=10, pady=10)

        # Reverse Compliance Entry
        self.label_compliacncer = ttk.Label(parameter_frame, text=self.config["rev_limit_label"])
        self.label_compliacncer.grid(row=6, column=0, padx=10, pady=10)
        self.entry_compliacncer = ttk.Entry(parameter_frame)
        self.entry_compliacncer.insert(0, "1")
        self.entry_compliacncer.grid(row=6, column=1, padx=10, pady=10)

        # NPLC (Number of Power Line Cycle) entry
        self.label_nplc = ttk.Label(parameter_frame, text="NPLC (Number of PLC):")
        self.label_nplc.grid(row=7, column=0, padx=10, pady=10)
        self.entry_nplc = ttk.Entry(parameter_frame)
        self.entry_nplc.insert(0, "1")
        self.entry_nplc.grid(row=7, column=1, padx=10, pady=10)

        # Pulse on Delay entry
        self.label_delay = ttk.Label(parameter_frame, text="[All Sweep] Hold_On_Delay(ms):")
        self.label_delay.grid(row=8, column=0, padx=10, pady=10)
        self.entry_delay = ttk.Entry(parameter_frame)
        self.entry_delay.insert(0, "50")
        self.entry_delay.grid(row=8, column=1, padx=10, pady=10)

        # Pulse off Delay entry
        self.label_off_delay = ttk.Label(parameter_frame, text="[Pulse Sweep] Pulse-OFF time (ms):")
        self.label_off_delay.grid(row=9, column=0, padx=10, pady=10)
        self.entry_off_delay = ttk.Entry(parameter_frame)
        self.entry_off_delay.grid(row=9, column=1, padx=10, pady=10)
        self.entry_off_delay.config(state="disabled")

        # Autorange Dropdown
        self.label_autorange = ttk.Label(parameter_frame, text="Measure autorange:")
        self.label_autorange.grid(row=10, column=0, padx=10, pady=10)
        self.autoranges = ["Off", "On", "Follow_Limit"]
        self.combo_autorange = ttk.Combobox(parameter_frame, values=self.autoranges, state="readonly")
        self.combo_autorange.set("On")
        self.combo_autorange.grid(row=10, column=1, padx=10, pady=10)
        self.combo_autorange.bind("<<ComboboxSelected>>", self.on_autorange_selected)

        # Measure Range entry
        self.label_range = ttk.Label(parameter_frame, text=self.config["measure_range_label"])
        self.label_range.grid(row=11, column=0, padx=10, pady=10)
        self.entry_range = ttk.Entry(parameter_frame)
        self.entry_range.insert(0, "1")
        self.entry_range.grid(row=11, column=1, padx=10, pady=10)
        self.entry_range.config(state="disabled")

        # Auto-Zero Dropdown
        self.label_autozero = ttk.Label(parameter_frame, text="Auto-Zero:")
        self.label_autozero.grid(row=12, column=0, padx=10, pady=10)
        self.autozeros = ["Off", "Once", "Auto"]
        self.combo_autozero = ttk.Combobox(parameter_frame, values=self.autozeros, state="readonly")
        self.combo_autozero.set("Auto")
        self.combo_autozero.grid(row=12, column=1, padx=10, pady=10)
        
        # Channel Dropdown
        self.label_channel = ttk.Label(parameter_frame, text="Channel:")
        self.label_channel.grid(row=13, column=0, padx=10, pady=10)
        self.channels = ["Channel A", "Channel B"]
        self.combo_channel = ttk.Combobox(parameter_frame, values=self.channels, state="readonly")
        self.combo_channel.set("Channel A")
        self.combo_channel.grid(row=13, column=1, padx=10, pady=10)

        # Sense Mode Dropdown
        self.label_sensemode = ttk.Label(parameter_frame, text="Sense Mode:")
        self.label_sensemode.grid(row=14, column=0, padx=5, pady=5)
        self.sensemodes = ["2-wire (Local)", "4-wire (Remote)"]
        self.combo_sensemode = ttk.Combobox(parameter_frame, values=self.sensemodes, state="readonly")
        self.combo_sensemode.set("2-wire (Local)")
        self.combo_sensemode.grid(row=14, column=1, padx=10, pady=10)
        self.combo_sensemode.bind("<<ComboboxSelected>>", self.on_sense_type_selected)

        # Sweep Type Dropdown
        self.label_sweep_type = ttk.Label(parameter_frame, text="Sweep Mode:")
        self.label_sweep_type.grid(row=15, column=0, padx=10, pady=10)
        self.sweep_types = ["Staircase", "Pulse"]
        self.combo_sweep_type = ttk.Combobox(parameter_frame, values=self.sweep_types, state="readonly")
        self.combo_sweep_type.set("Staircase")
        self.combo_sweep_type.grid(row=15, column=1, padx=10, pady=10)
        self.combo_sweep_type.bind("<<ComboboxSelected>>", self.on_sweep_type_selected)

        # Label for Sweep Type Image
        self.image_header = ttk.Label(image_frame, text="Sweep type", font=header_font2)
        self.image_header.grid(row=0, column=0, padx=10, pady=10)

        self.image_label = ttk.Label(image_frame)
        self.image_label.grid(row=1, column=0, padx=10, pady=10)
        image = Image.open('./Image/Staircase.PNG')
        tk_image = ImageTk.PhotoImage(image.resize((400, 300)))
        self.image_label.configure(image=tk_image)
        self.image_label.image = tk_image

        # Label for SENSE Type Image
        self.image_header2 = ttk.Label(image_frame, text="Sense mode", font=header_font2)
        self.image_header2.grid(row=3, column=0, padx=10, pady=10)
        self.image2_label = ttk.Label(image_frame)
        self.image2_label.grid(row=4, column=0, padx=10, pady=10)
        image2 = Image.open('./Image/2wire.PNG')
        tk_image2 = ImageTk.PhotoImage(image2.resize((400, 300)))
        self.image2_label.configure(image=tk_image2)
        self.image2_label.image = tk_image2

        # Detail Header
        self.header_detail = ttk.Label(detail_frame, text="Detail Block", font=header_font)
        self.header_detail.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Module Name Entry
        self.label_module_name = ttk.Label(detail_frame, text="Module Name:")
        self.label_module_name.grid(row=1, column=0, padx=10, pady=10)
        self.entry_module_name = ttk.Entry(detail_frame)
        self.entry_module_name.grid(row=1, column=1, padx=10, pady=10)

        # Measurement Type Entry
        self.label_measurementType = ttk.Label(detail_frame, text="Measurement type:")
        self.label_measurementType.grid(row=2, column=0, padx=10, pady=10)
        self.entry_measurementType = ttk.Entry(detail_frame)
        self.entry_measurementType.grid(row=2, column=1, padx=10, pady=10)

        # Probing method Entry
        self.label_probing = ttk.Label(detail_frame, text="Probe point:")
        self.label_probing.grid(row=3, column=0, padx=10, pady=10)
        self.entry_probing = ttk.Entry(detail_frame)
        self.entry_probing.grid(row=3, column=1, padx=10, pady=10)

        self.probe_types = self.pin_list
        self.combo_probing = ttk.Combobox(detail_frame, values=self.probe_types, state="readonly")
        self.combo_probing.bind("<<ComboboxSelected>>", self.probe_IO)
    
        self.CheckVar2=tk.IntVar()
        self.AutoConfig_check = ttk.Checkbutton(detail_frame, text="Auto Setting ?", variable=self.CheckVar2, command=self.toggle_AutoSet)
        self.AutoConfig_check.grid(row=3, column=2, padx=10, pady = 10)

        # File name Entry
        self.label_filename = ttk.Label(detail_frame, text="File_name:")
        self.label_filename.grid(row=4, column=0, padx=10, pady=10)
        self.entry_filename = ttk.Entry(detail_frame)
        self.entry_filename.grid(row=4, column=1, padx=10, pady=10)

        # Beep Check box
        self.CheckVar1 = tk.IntVar()
        self.beep_check = ttk.Checkbutton(action_frame, text="Beep ?", variable=self.CheckVar1)
        self.beep_check.grid(row=0, column=0, padx=10, pady=10)
        self.CheckVar1.set(1)

        # Button to Start Measurement
        self.button_start = ttk.Button(action_frame, text="Start Measurement", command=self.threading)
        self.button_start.grid(row=0, column=1, padx=10, pady=10)

        # Button to Stop Measurement
        self.button_abort = ttk.Button(action_frame, text="Abort", command=self.abort, state=tk.DISABLED)
        self.button_abort.grid(row=0, column=2, padx=10, pady=10)

        # Button to Export to JMP
        self.button_jmp = ttk.Button(action_frame, text="Export to JMP", command=self.export_jmp)
        self.button_jmp.grid(row=0, column=3, padx=10, pady=10)

        # Button to Delete old data
        self.button_del = ttk.Button(action_frame, text="Delete old data", command=self.delete_old)
        self.button_del.grid(row=0, column=4, padx=10, pady=10)

        # Button to Close Measurement
        self.button_close = ttk.Button(action_frame, text="Close", command=self.close_window)
        self.button_close.grid(row=0, column=5, padx=10, pady=10)

    def threading(self):
        self.event.clear()
        t1 = Thread(target=self.start_measurement)
        t1.daemon = True
        t1.start()

    def toggle_AutoSet(self):
        if self.CheckVar2.get():
            self.entry_probing.grid_remove()
            self.combo_probing.grid(row=3, column=1, padx=10, pady=10)
        else :
            self.combo_probing.grid_remove()            
            self.entry_probing.grid(row=3, column=1, padx=10, pady=10)
            self.entry_start.config(state= "enabled")
            self.entry_stop.config(state= "enabled")

    def on_sweep_type_selected(self, event):
        selected_type = self.combo_sweep_type.get()
        if selected_type == "Staircase":
            self.show_image('./Image/Staircase.PNG')
            self.entry_off_delay.config(state="disabled")
        elif selected_type == "Pulse":
            self.show_image('./Image/Pulse.PNG')
            self.entry_off_delay.config(state="enabled")
    
    def on_sense_type_selected(self, event):
        selected_type = self.combo_sensemode.get()
        if selected_type == "2-wire (Local)":
            self.show_image2('./Image/2wire.PNG')
        elif selected_type == "4-wire (Remote)":
            self.show_image2('./Image/4wire.PNG')

    def on_interface_selected(self,event):
        interface_selected = self.combo_interface.get()
        if interface_selected == "GPIB":
            self.entry_interface.delete(0,tk.END)
            self.entry_interface.insert(0,"26")
        elif interface_selected == "Serial Interface":
            self.entry_interface.delete(0,tk.END)                                                       

    def on_autorange_selected(self, event):
        autorange_selected = self.combo_autorange.get()
        if autorange_selected == "Off":
            self.entry_range.config(state="enabled")
        else:
            self.entry_range.config(state="disabled")

    def probe_IO(self,event):
        tmp_index = self.pin_list.index(self.combo_probing.get())
        if self.sourcetype == "Voltage source":
            val_min = self.vinmin_list[tmp_index]
            val_pl = self.vinpl_list[tmp_index]
            comp = self.icomp_list[tmp_index]
        else:
            val_min = self.cinmin_list[tmp_index]
            val_pl = self.cinpl_list[tmp_index]
            comp = self.vcomp_list[tmp_index]

        self.entry_start.delete(0,tk.END)
        self.entry_stop.delete(0,tk.END)        
        self.entry_compliacncef.delete(0,tk.END)         
        self.entry_start.insert(0,val_min)
        self.entry_stop.insert(0,val_pl)
        self.entry_compliacncef.insert(0,comp)

    def abort(self):
        interface_address = self.entry_interface.get()
        keithley = None
        if self.combo_interface.get() == "GPIB":
            keithley = self.rm.open_resource(f'GPIB::{interface_address}::INSTR')
        elif self.combo_interface.get() == "Serial Interface":
            keithley = self.rm.open_resource(interface_address)
            
        if keithley is None:
            raise ConnectionError(f"Failed to connect to the instrument. Interface type: {self.combo_interface.get()}, Address: {interface_address}")
        
        channel = self.combo_channel.get()
        if channel == "Channel A":
            keithley.write("smua.reset()")
            print("Channel A abort")
        elif channel == "Channel B":
            keithley.write("smub.reset()")
            print("Channel B abort")
        self.event.set()
        keithley.write("beeper.beep(0.5,2000)")
        keithley.close()

    def plot(self):
        filename = self.entry_filename.get()
        result_path = os.getcwd() + "/Output/" + filename + ".csv"
        
        if not os.path.exists(result_path):
            print("No result file found to plot.")
            return

        df_result = pd.read_csv(result_path)
        
        self.ax.clear()
        self.plot_data = []

        for label in df_result['Label'].unique():
            label_data = df_result[df_result['Label'] == label]
            Module_name = label_data['SerialNumber'].iloc[0]
            Probe_point = label_data['Pin'].iloc[0]
            voltages = label_data['Voltage[V]'].tolist()
            currents = label_data['Current[mA]'].tolist()
            color = self.colors[len(self.plot_data) % len(self.colors)]
            
            if self.sourcetype == "Voltage source":
                self.plot_data.append((voltages, currents, color, label))
                self.ax.plot(voltages, currents, color=color, label=f"{label}, SN:{Module_name}, Pin:{Probe_point})")
            else:
                self.plot_data.append((currents, voltages, color, label))
                self.ax.plot(currents, voltages, color=color, label=f"{label}, SN:{Module_name}, Pin:{Probe_point})")

        self.ax.set_yscale('log')
        self.ax.set_xlabel(self.config["plot_xlabel"])
        self.ax.set_ylabel(self.config["plot_ylabel"])
        self.ax.set_title(self.config["plot_title"])
        self.ax.legend(loc='upper right')
        self.canvas.draw()

    def close_window(self):
        if os.path.isfile(os.getcwd() + "/Output/tmp_del.csv"):
            os.remove(os.getcwd() + "/Output/tmp_del.csv")
        if self.main_window is not None:
            self.main_window.destroy()

    def interface_check(self) :
        interface_type = self.combo_interface.get()
        try:
            interface_address = self.entry_interface.get()
            if interface_type == "GPIB":
                resource_string = f'GPIB::{interface_address}::INSTR'
            elif interface_type == "Serial Interface":
                resource_string = interface_address
            else:
                print("Invalid interface type selected.")
                return

            keithley = self.rm.open_resource(resource_string)
            print(f'Successfully connected to: {keithley.query("*IDN?")}')
            keithley.write("beeper.beep(0.1,2500)")
            keithley.close()
        except Exception as e:
            print(f"Connection failed: {e}")
      
    def export_jmp(self):
        def path_update():
            file_path = filedialog.askopenfilename(initialdir="C:/",filetypes=[("Executable files", "*.exe")])
            if file_path:
                with open(self.json_path,'r') as file:
                    data = json.load(file)
                data["JMP_dir"] = file_path
                with open(self.json_path, 'w', encoding='utf-8') as file:
                    json.dump(data,file,ensure_ascii=False,indent= 2)
                self.jmp_label.configure(text = file_path)

        def run_jmp():
            filename = self.entry_filename.get()
            jmp_dir = self.jmp_label.cget("text")
            script_dir = self.script_label.cget("text")        
            result_path = os.getcwd() + "/Output/" + filename + ".csv"
            df_tmp = pd.read_csv(result_path)
            df_tmp.to_csv(os.getcwd() + "/Output/tmp.csv")

            try:
                subprocess.call([jmp_dir, os.getcwd() + script_dir])
                while not os.path.exists(os.getcwd() + "/Output/JMPScriptCompleted.txt"):
                    time.sleep(1)
                os.remove(os.getcwd() + "/Output/tmp.csv")
                os.remove(os.getcwd() + "/Output/JMPScriptCompleted.txt")
                print("Export to JMP finished")
            except Exception as e:
                print(f"Cannot open JMP: {e}")
                if os.path.exists(os.getcwd() + "/Output/tmp.csv"):
                    os.remove(os.getcwd() + "/Output/tmp.csv")

        with open(self.json_path, 'r') as file:
            data = json.load(file)
            jmp_path = data["JMP_dir"]
            script_path_key = "VI_Script" if self.sourcetype == "Voltage source" else "IV_Script"
            script_path = data[script_path_key]

        jmp_window = tk.Toplevel()
        jmp_window.grab_set()
        jmp_window.title("Export to JMP")
        
        ttk.Button(jmp_window, text="JMP Path",command=path_update).grid(row=0, column=0, padx=20, pady=20)
        self.jmp_label = ttk.Label(jmp_window, text=jmp_path)
        self.jmp_label.grid(row=0, column=1, padx=20, pady=20)
        
        ttk.Button(jmp_window, text = "Script Path").grid(row=1, column=0, padx=20, pady=20) 
        self.script_label = ttk.Label(jmp_window, text=script_path)
        self.script_label.grid(row=1, column=1, padx=20, pady=20)
        
        ttk.Button(jmp_window, text='Run', command=run_jmp).grid(row=2, column=0, padx=20, pady=20)
        ttk.Button(jmp_window,text='Cancel', command=jmp_window.destroy).grid(row=2, column=1, padx=20, pady=20)

    def delete_old(self):
        def confirm_deletion(selection):
            try:
                selection = int(selection.strip('[] '))
                filename = self.entry_filename.get()
                result_path = os.getcwd() + "/Output/" + filename + ".csv"
                df_result = pd.read_csv(result_path)

                df_result = df_result[df_result['Label'] != selection]
                df_result.to_csv(result_path, index=False)
                print(f"Data with label {selection} deleted successfully.")
                
                self.plot()
            except (ValueError, FileNotFoundError) as e:
                print(f"Error during deletion: {e}")
            deletion_window.destroy()

        filename = self.entry_filename.get()
        result_path = os.getcwd() + "/Output/" + filename + ".csv"
        if not os.path.exists(result_path):
            print("Result file does not exist.")
            return
            
        df_result = pd.read_csv(result_path)
        labels = df_result['Label'].unique()

        deletion_window = tk.Toplevel()
        deletion_window.title("Delete Old Data")
        ttk.Label(deletion_window, text="Choose a label to delete:").pack(padx=20, pady=10)

        labels_cleaned = [str(label).strip('[] ') for label in labels]

        selected_label = tk.StringVar()
        combobox = ttk.Combobox(deletion_window, textvariable=selected_label, values=labels_cleaned, state="readonly")
        combobox.pack(padx=20, pady=10)
        ttk.Button(deletion_window, text="OK", command=lambda: confirm_deletion(selected_label.get())).pack(padx=20, pady=10)

    def show_image(self, image_path):
        image = Image.open(image_path)
        tk_image = ImageTk.PhotoImage(image.resize((400, 300)))
        self.image_label.configure(image=tk_image)
        self.image_label.image = tk_image

    def show_image2(self, image_path):
        image = Image.open(image_path)
        tk_image = ImageTk.PhotoImage(image.resize((400, 300)))
        self.image2_label.configure(image=tk_image)
        self.image2_label.image = tk_image

    def start_measurement(self):
        # This method should be overridden by subclasses
        raise NotImplementedError("Subclasses must implement start_measurement")
