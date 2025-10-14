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



class VISweep(ttk.Frame):
    
    rm = visa.ResourceManager()

    def __init__(self, master, main_window = None):
        # self = master
        super().__init__(master)
        self.main_window = main_window
        self.event = Event()
        self.json_path = 'Config.json'
        self.sourcetype = "Voltage source"
        # master.title("IV Curve Measurement " + Version)
        # super().__init__(master)
        # print("##############################################################")
        # print(f"Version : {Version}")
        # print("##############################################################")

        self.df_config = pd.read_csv('Auto_Config_VSource.csv')
        self.pin_list = self.df_config['Pin_Total'].to_list()
        self.vinmin_list = self.df_config['Voltage_-'].to_list()
        self.vinpl_list = self.df_config['Voltage_+'].to_list()
        self.icomp_list = self.df_config['Current_Comp'].to_list()
        
        


        self.devlist = self.rm.list_resources()
        # rm = visa.ResourceManager()
        # print("Serial INST : ", self.devlist)
        # print('Pin_list : ', self.pin_list )
        # print('vinmin_list : ', self.vinmin_list )
        # print('vinpl_list : ', self.vinpl_list )


        self.create_widgets()
        self.colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        self.plot_data = []
        self.create_widgets()

    def create_widgets(self):
        # Parameter Block
        parameter_frame = ttk.Frame(self)
        parameter_frame.grid(row=0, column=0, padx=10, pady=10)

        # Detail Block
        detail_frame = ttk.Frame(self)
        detail_frame.grid(row=1, column=0, padx=10, pady=10)
        header_font = tkinter.font.Font(family="Arial", weight="bold", size=15)
        header_font2 = tkinter.font.Font(family="Arial", weight="bold", size=11)

        # Frame for Image
        image_frame = ttk.Frame(self)
        image_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10)

        # Frame for Action button
        action_frame = ttk.Frame(self)
        action_frame.grid(row=2, column=0, columnspan=2)

        # Frame for IV plot
        plot_frame = ttk.Frame(self)
        plot_frame.grid(row=0, column=2, rowspan=2, padx=3, pady=3)

        # Label for plot
        self.plot_header = ttk.Label(plot_frame, text="IV plot", font=header_font2)
        self.plot_header.grid(row=0, column=0, padx=10, pady=10)

        # Blank plot
        self.fig = plt.figure(figsize=(5, 5), dpi=130)
        self.ax = self.fig.add_axes([0.1, 0.1, 0.8, 0.8])
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=10)

        # Parameter Header
        self.header_parameter = ttk.Label(parameter_frame, text="Voltage Source Parameter", font=header_font)
        self.header_parameter.grid(row=0, column=0, padx=10, pady=10, sticky="w")


        # Instrument Address Entry
        self.interface_type = ["GPIB", "Serial Interface"]
        self.combo_interface = ttk.Combobox(parameter_frame, values=self.interface_type, state="readonly")
        self.combo_interface.grid(row=1, column=0, padx=3, pady=10)
        self.combo_interface.bind("<<ComboboxSelected>>", self.on_interface_selected)
    
   

        self.entry_interface = ttk.Entry(parameter_frame)
        # self.entry_interface.insert(0, "26")
        self.entry_interface.grid(row=1, column=1, padx=3, pady=10)

        # Interface Check Button
        self.button_interface_check = ttk.Button(parameter_frame, text="Interface Check", command=self.interface_check)
        self.button_interface_check.grid(row=1, column=2, padx=3, pady=10)
        # Start Voltage Entry
        self.label_start_voltage = ttk.Label(parameter_frame, text="Start Voltage (V):")
        self.label_start_voltage.grid(row=2, column=0, padx=10, pady=10)
        self.entry_start_voltage = ttk.Entry(parameter_frame)
        self.entry_start_voltage.insert(0, "-3")
        self.entry_start_voltage.grid(row=2, column=1, padx=10, pady=10)

        # Stop Voltage Entry
        self.label_stop_voltage = ttk.Label(parameter_frame, text="Stop Voltage (V):")
        self.label_stop_voltage.grid(row=3, column=0, padx=10, pady=10)
        self.entry_stop_voltage = ttk.Entry(parameter_frame)
        self.entry_stop_voltage.insert(0, "3")
        self.entry_stop_voltage.grid(row=3, column=1, padx=10, pady=10)

        # Step Voltage Entry
        self.label_step_voltage = ttk.Label(parameter_frame, text="Step (V):")
        self.label_step_voltage.grid(row=4, column=0, padx=10, pady=10)
        self.entry_step_voltage = ttk.Entry(parameter_frame)
        self.entry_step_voltage.insert(0, "0.1")
        self.entry_step_voltage.grid(row=4, column=1, padx=10, pady=10)

        # Forward Compliance Current entry
        self.label_compliacncef = ttk.Label(parameter_frame, text="Forward Limit (mA):")
        self.label_compliacncef.grid(row=5, column=0, padx=10, pady=10)
        self.entry_compliacncef = ttk.Entry(parameter_frame)
        self.entry_compliacncef.insert(0, "1")
        self.entry_compliacncef.grid(row=5, column=1, padx=10, pady=10)

        # Reverse Compliance Current entry
        self.label_compliacncer = ttk.Label(parameter_frame, text="Reverse Limit (mA):")
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
        self.label_range = ttk.Label(parameter_frame, text="Measure range (mA):")
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
        # self.combo_probing.grid(row=3, column=1, padx=10, pady=10)
        self.combo_probing.bind("<<ComboboxSelected>>", self.probe_IO)
    





        self.CheckVar2=tk.IntVar()
        self.AutoConfig_check = ttk.Checkbutton(detail_frame, text="Auto Setting ?", variable=self.CheckVar2, command=self.toggle_AutoSet)
        self.AutoConfig_check.grid(row=3, column=2, padx=10, pady = 10)
        # self.CheckVar2.set(1)

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
            # self.entry_start_voltage.config(state= "disabled")
            # self.entry_stop_voltage.config(state= "disabled")

        else :
            self.combo_probing.grid_remove()            
            self.entry_probing.grid(row=3, column=1, padx=10, pady=10)
            self.entry_start_voltage.config(state= "enabled")
            self.entry_stop_voltage.config(state= "enabled")
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
        # print('selected interface : ', interface_selected)
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
        vinmin = self.vinmin_list[tmp_index]
        vinpl = self.vinpl_list[tmp_index]
        icomp = self.icomp_list[tmp_index]

        print('tmp_index : ',tmp_index)
        print('vinmin : ',vinmin)
        print('vinpl : ',vinpl)
        print('icomp : ', icomp)




        self.entry_start_voltage.delete(0,tk.END)
        self.entry_stop_voltage.delete(0,tk.END)        
        self.entry_compliacncef.delete(0,tk.END)         
        self.entry_start_voltage.insert(0,vinmin)
        self.entry_stop_voltage.insert(0,vinpl)
        self.entry_compliacncef.insert(0,icomp)

    def abort(self):
        # self.evt.set() 
        interface_address = self.entry_interface.get()

        keithley = None  # Initialize keithley variable
        
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











    def IVplot(self):
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
            self.plot_data.append((voltages, currents, color, label))
            self.ax.plot(voltages, currents, color=color, label=f"{label}, SN:{Module_name}, Pin:{Probe_point})")

        self.ax.set_yscale('log')
        self.ax.set_xlabel('Voltage (V)')
        self.ax.set_ylabel('Current (mA)')
        self.ax.set_title('IV Curve (V-mA)')
        self.ax.legend(loc='upper right')
        self.canvas.draw()

    def close_window(self):
        if os.path.isfile(os.getcwd() + "/Output/tmp_del.csv"):
            os.remove(os.getcwd() + "/Output/tmp_del.csv")
        else:
            pass                      
        # root.destroy()

        if self.main_window is not None:
            self.main_window.destroy()


    def interface_check(self) :
        interface_type = self.combo_interface.get()
        print('interface_type : ', interface_type)
        
        if interface_type == "GPIB":
            try:
                interface_address = self.entry_interface.get()
                keithley = self.rm.open_resource(f'GPIB::{interface_address}::INSTR')
                print(f'Successfully connected to instrument through GPIB {interface_address}: ', keithley.query('*IDN?'))
                keithley.write("beeper.beep(0.1,2500)")
                keithley.close()



            except Exception as e:
                print("No SMU Connected")
      
        elif interface_type == "Serial Interface":
            try:
                interface_address = self.entry_interface.get()
                # rm = visa.ResourceManager()
                keithley = self.rm.open_resource(interface_address) # Trial to connect the instrument
                print(f'Successfully connect instrument through Serial address {interface_address} : ', keithley.query('*IDN?')) # Ask and get the identification of the instrument
                keithley.write("beeper.beep(0.1,2500)")
                keithley.close()


            except:
                print("No SMU Connected")           
        
    def export_jmp(self):

        def path_update():
            # path = filedialog.askopenfilename()
            # self.entry_start_voltage.delete(0, tk.END)
            # self.entry_start_voltage.insert(0, path)

            self.file_path = filedialog.askopenfilename(initialdir="C:/",filetypes=[("Executable files", "*.exe")])
            if self.file_path:
                # self.jmp_path = self.file_path
        
                with open(self.json_path,'r') as file :
                    data = json.load(file)

                
                data["JMP_dir"] = self.file_path
                    
                with open(self.json_path, 'w', encoding='utf-8') as file:
                    json.dump(data,file,ensure_ascii=False,indent= 2)
            # print('self.file_path : ',self.file_path)

            self.jmp_label.configure(text = self.file_path)

        def run_jmp():
 
            filename = self.entry_filename.get()
            jmp_dir = self.jmp_label.cget("text")
            script_dir = self.script_label.cget("text")        
            result_path = os.getcwd() + "/Output/" + filename + ".csv"
            df_tmp = pd.read_csv(result_path)
            df_tmp.to_csv(os.getcwd() + "/Output/tmp.csv")


            with open(self.json_path, 'r') as file:
                data = json.load(file)
                self.jmp_path = data["JMP_dir"]
                self.iv_script = data["VI_Script"]
            try:
                subprocess.call([jmp_dir, os.getcwd() + script_dir])
                while not os.path.exists(os.getcwd() + "/Output/JMPScriptCompleted.txt"):
                    time.sleep(1)
                os.remove(os.getcwd() + "/Output/tmp.csv")
                os.remove(os.getcwd() + "/Output/JMPScriptCompleted.txt")
                print("Export to JMP finished")
            except Exception as e:
                print("Cannot open JMP... Check JMP path or install JMP first")
                os.remove(os.getcwd() + "/Output/tmp.csv")


        with open(self.json_path, 'r') as file:
            data = json.load(file)
            self.jmp_path = data["JMP_dir"]
            self.iv_script = data["VI_Script"]
            # print("JMP path from json : ", self.jmp_path)
            # print("IV script from json : ", self.iv_script)

        jmp_window = tk.Toplevel()
        jmp_window.grab_set()

        jmp_window.title("Export to JMP")
        ttk.Button(jmp_window, text="JMP Path",command=path_update).grid(row=0, column=0, padx=20, pady=20)
        self.jmp_label = ttk.Label(jmp_window, text=self.jmp_path)
        self.jmp_label.grid(row=0, column=1, padx=20, pady=20)
        
        ttk.Button(jmp_window, text = "Script Path").grid(row=1, column=0, padx=20, pady=20) 
        self.script_label = ttk.Label(jmp_window, text=self.iv_script)
        self.script_label.grid(row=1, column=1, padx=20, pady=20)
        ttk.Button(jmp_window, text='Run', command=run_jmp).grid(row=2, column=0, padx=20, pady=20)
        ttk.Button(jmp_window,text='Cancel', command=jmp_window.destroy).grid(row=2, column=1, padx=20, pady=20)



        # text="Export to JMP", 


        # try:
        #     subprocess.call([r"C:\Program Files\SAS\JMP\16\jmp.exe", os.getcwd() + r"/IV_Plot_Generator_exe.jsl"])
        #     while not os.path.exists(os.getcwd() + "/Output/JMPScriptCompleted.txt"):
        #         time.sleep(1)
        #     os.remove(os.getcwd() + "/Output/tmp.csv")
        #     os.remove(os.getcwd() + "/Output/JMPScriptCompleted.txt")
        #     print("Export to JMP finished")
        # except Exception as e:
        #     print("Cannot open JMP... Check JMP path or install JMP first")
        #     os.remove(os.getcwd() + "/Output/tmp.csv")

    def delete_old(self):
        def confirm_deletion(selection):
            try:
                selection = int(selection.strip('[] '))
                filename = self.entry_filename.get()
                result_path = os.getcwd() + "/Output/" + filename + ".csv"
                df_result = pd.read_csv(result_path)

                # Remove data from DataFrame and save it
                df_result = df_result[df_result['Label'] != selection]
                df_result.to_csv(result_path, index=False)
                print(f"Data with label {selection} deleted successfully.")
                
                # Update plot
                self.IVplot()
            except ValueError:
                print("Invalid selection for deletion.")
            deletion_window.destroy()

        filename = self.entry_filename.get()
        result_path = os.getcwd() + "/Output/" + filename + ".csv"
        df_result = pd.read_csv(result_path)
        labels = df_result['Label'].unique()

        deletion_window = tk.Toplevel()
        deletion_window.title("Delete Old Data")
        ttk.Label(deletion_window, text="Choose a label to delete:").pack(padx=20, pady=10)

        labels_cleaned = [str(label).strip('[] ') for label in labels]  # Clean the labels

        selected_label = tk.StringVar()
        combobox = ttk.Combobox(deletion_window, textvariable=selected_label, values=labels_cleaned)
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
        if os.path.isfile(os.getcwd() + "/Output/tmp_del.csv"):
            os.remove(os.getcwd() + "/Output/tmp_del.csv")
        
        self.button_abort['state'] = tk.NORMAL
        print("Start IV Sweep.... ")
        start = time.time()
        
        interface_address = self.entry_interface.get()
        autorange_selected = self.combo_autorange.get()
        selected_type = self.combo_sweep_type.get()
        start_voltage = float(self.entry_start_voltage.get())
        stop_voltage = float(self.entry_stop_voltage.get())
        step_voltage = float(self.entry_step_voltage.get())
        comp_currentf = float(self.entry_compliacncef.get())
        comp_currentr = float(self.entry_compliacncer.get())
        nplc = float(self.entry_nplc.get())
        selected_channel = self.combo_channel.get()
        selected_sensemode = self.combo_sensemode.get()
        filename = self.entry_filename.get()
        module_SN = self.entry_module_name.get()
        if self.CheckVar2.get():
            probe_point = self.combo_probing.get()
        else :
            probe_point = self.entry_probing.get()
        measurementType = self.entry_measurementType.get()
        on_delay = self.entry_delay.get()
        off_delay = self.entry_off_delay.get()
        autozero = self.combo_autozero.get()

        result_path = os.getcwd() + "/Output/" + filename + ".csv"
        tmp_del_path = os.getcwd() + "/Output/tmp_del.csv"
        
        comp_currentf = comp_currentf / 1000
        comp_currentr = comp_currentr / 1000

        # Open connection to the GPIB instrument
        # rm = visa.ResourceManager()
        keithley = None

        if self.combo_interface.get() == "GPIB":
            keithley = self.rm.open_resource(f'GPIB::{interface_address}::INSTR')
        elif self.combo_interface.get() == "Serial Interface":
            keithley = self.rm.open_resource(interface_address)
        
        if keithley is None:
            raise ConnectionError(f"Failed to connect to the instrument. Interface type: {self.combo_interface.get()}, Address: {interface_address}")
    
        if off_delay == "":
            off_delay = "nan"
        else:
            off_delay = float(off_delay) / 1000

        if selected_sensemode == "2-wire (Local)":
            selected_sensemode = 0
        else:
            selected_sensemode = 1

        if autozero == "Off":
            autozero = "AUTOZERO_OFF"
        elif autozero == "Once":
            autozero = "AUTOZERO_ONCE"
        else:
            autozero = "AUTOZERO_AUTO"

        if selected_type == "Staircase":
            off_delay = "nan"
        elif selected_type == "Pulse":
            off_delay = float(self.entry_off_delay.get())



        # self.autoranges = ["Off", "On", "Follow_Limit"]        
        if autorange_selected == "Off":
            mrange = float(self.entry_range.get()) / 1000
            autorange = 0
        elif autorange_selected == "On":
            mrange = "nan"
            autorange = 1
        elif autorange_selected == "Follow_Limit":
            mrange = "nan"
            autorange = 2

        print('Initialize ... ')
        self.setup_measurement(keithley, selected_channel, selected_sensemode, nplc, autozero, autorange, mrange)

        if selected_type == "Staircase":
            voltages, currents = self.measure_iv_curve_staircase(keithley, selected_channel, start_voltage, stop_voltage, step_voltage, comp_currentf, comp_currentr, on_delay)
        elif selected_type == "Pulse":
            voltages, currents = self.measure_iv_curve_pulse(keithley, selected_channel, start_voltage, stop_voltage, step_voltage, comp_currentf, comp_currentr, on_delay, off_delay)  

        # Print or further process the collected data
        for voltage, current in zip(voltages, currents):
            print(f"Voltage: {voltage} V, Current: {current} A")

        # voltage = [i for i in np.arange(-3,3,0.1)]
        # current = [j for j in np.arange(-3,3,0.1)]
        # current_raw_mA = [float(x)*1000 for x in currents]
        current_abs = [abs(float(x)) for x in currents]
        current_abs_mA = [float(x) * 1000 for x in current_abs]
        N_measure = len(voltages)
        end = time.time()
        elapsed_time = end - start 
        print("Elapsed Time : %f s" % elapsed_time + "\n")

        if not os.path.exists(result_path):
            print(f"No File found... Create a new one : {filename}.csv")
            df = pd.DataFrame({"Label": [1] * N_measure, "Sourcetype" : [self.sourcetype]* N_measure, "SerialNumber": [module_SN] * N_measure, "Measurement_type": [measurementType] * N_measure, "Channel": [selected_channel] * N_measure,
                               "Sense_mode": [selected_sensemode] * N_measure, "Sweep_Type": [selected_type] * N_measure, "Forward_Limit(mA)": [1000 * float(comp_currentf)] * N_measure,
                               "Reverse_Limit(mA)": [1000 * float(comp_currentr)] * N_measure, "Hold_On_Delay(ms)": [on_delay] * N_measure, "Pulse_Off_Time(ms)": [off_delay] * N_measure,
                               "Autorange": [autorange_selected] * N_measure, "Measure_Range(mA)": [mrange * 1000] * N_measure, "Autozero": [autozero] * N_measure,
                               "Pin": [probe_point] * N_measure, "Voltage[V]": voltages, "Current[A]": current_abs, "Current[mA]": current_abs_mA, "NPLC": [nplc] * N_measure})
            df_result = df.copy()
            df_result.to_csv(result_path, index=False)
            df_result.to_csv(tmp_del_path, index=False)
        else:
            print(f"{filename}.csv already exists .. Overwrite the result on it")
            df = pd.read_csv(result_path)
            max_label = df['Label'].max()
            df2 = pd.DataFrame({"Label": [max_label + 1] * N_measure, "Sourcetype" : [self.sourcetype]* N_measure, "SerialNumber": [module_SN] * N_measure, "Measurement_type": [measurementType] * N_measure,
                                "Channel": [selected_channel] * N_measure, "Sense_mode": [selected_sensemode] * N_measure, "Sweep_Type": [selected_type] * N_measure,
                                "Forward_Limit(mA)": [1000 * float(comp_currentf)] * N_measure, "Reverse_Limit(mA)": [1000 * float(comp_currentr)] * N_measure,
                                "Hold_On_Delay(ms)": [on_delay] * N_measure, "Pulse_Off_Time(ms)": [off_delay] * N_measure, "Autorange": [autorange_selected] * N_measure,
                                "Measure_Range(mA)": [mrange * 1000] * N_measure, "Autozero": [autozero] * N_measure, "Pin": [probe_point] * N_measure,
                                "Voltage[V]": voltages, "Current[A]": current_abs, "Current[mA]": current_abs_mA, "NPLC": [nplc] * N_measure})
            df2.to_csv(tmp_del_path, index=False)
            df_result = pd.concat([df, df2], axis=0)
            df_result.to_csv(result_path, index=False)

        self.IVplot()
        print("IV measurement finished and saved successfully")
        print("##############################################################")
        self.button_abort['state'] = tk.DISABLED
        keithley.close()

    def setup_measurement(self, keithley, channel="Channel A", sensemode=0, nplc=1, autozero="AUTOZERO_AUTO", autorange=1, mrange="nan"):
        if channel == "Channel A":
            print("Init SMU Channel A ... ")
            keithley.write("smua.reset()")
            keithley.write("display.screen = 0")
            keithley.write("smua.sense = " + str(sensemode))
            keithley.write("smua.source.func = smua.OUTPUT_DCVOLTS")
            keithley.write("smua.source.autorangev = 1")
            if str(autorange) == "1":
                keithley.write("smua.measure.autorangei = 1")
            elif str(autorange) == "2":
                keithley.write("smua.measure.autorangei = 2")
            elif str(autorange) == "0":
                keithley.write("smua.measure.autorangei = 0")
                keithley.write("smua.measure.rangei = " + str(mrange))
            keithley.write("smua.measure.autozero = smua." + str(autozero))
            keithley.write("smua.measure.interval = 0")
            keithley.write("smua.measure.count = 1")
            keithley.write("smua.source.delay = smua.DELAY_OFF")
            keithley.write("smua.measure.delay = smua.DELAY_OFF")
            keithley.write("display.smua.measure.func = display.MEASURE_DCAMPS ")
            keithley.write("smua.measure.nplc = " + str(nplc))
        else:
            print("Init SMU Channel B ... ")
            keithley.write("smub.reset()")
            keithley.write("display.screen = 1")
            keithley.write("smub.sense = " + str(sensemode))
            keithley.write("smub.source.func = smub.OUTPUT_DCVOLTS")
            keithley.write("smub.source.autorangev = 1")
            if str(autorange) == "1":
                keithley.write("smub.measure.autorangei = 1")
            elif str(autorange) == "2":
                keithley.write("smub.measure.autorangei = 2")
            elif str(autorange) == "0":
                keithley.write("smub.measure.autorangei = 0")
                keithley.write("smub.measure.rangei = " + str(mrange))
            keithley.write("smub.measure.autozero = smub." + str(autozero))
            keithley.write("smub.measure.interval = 0")
            keithley.write("smub.measure.count = 1")
            keithley.write("smub.source.delay = smub.DELAY_OFF")
            keithley.write("smub.measure.delay = smub.DELAY_OFF")
            keithley.write("display.smub.measure.func = display.MEASURE_DCAMPS")
            keithley.write("smub.measure.nplc = " + str(nplc))
        print("Init SMU finished..")

    def measure_iv_curve_staircase(self, keithley, channel, start_voltage, stop_voltage, step_voltage, comp_currentf, comp_currentr, on_delay):
        voltages = []
        currents = []
        beep = self.CheckVar1.get()
        if beep == 1:
            print("Beep ON")
            keithley.write("beeper.beep(0.1,2000)")
        else:
            print("Beep OFF")

        for voltage in np.arange(start_voltage, stop_voltage + step_voltage, step_voltage):

            if channel == "Channel A":
                if voltage < 0:
                    keithley.write("smua.source.limiti = " + str(comp_currentr))
                else:
                    keithley.write("smua.source.limiti = " + str(comp_currentf))
                keithley.write("smua.source.levelv = " + str(voltage))
                keithley.write("smua.source.output = smua.OUTPUT_ON")
                time.sleep(float(on_delay) / 1000)
                keithley.write("smua.measure.i(smua.nvbuffer1)")
                current = keithley.query("printbuffer(1,1,smua.nvbuffer1.readings)")
                print("Current measured : ", current)
                currents.append(current)
                voltages.append(voltage)

            else:
                if voltage < 0 :
                    keithley.write("smub.source.limiti = " + str(comp_currentr))

                else :
                    keithley.write("smub.source.limiti = " + str(comp_currentf))

                keithley.write("smub.source.levelv = " + str(voltage))
                keithley.write("smub.source.output = smub.OUTPUT_ON")
                time.sleep(float(on_delay) / 1000)
                keithley.write("smub.measure.i(smub.nvbuffer1)")
                current = keithley.query("printbuffer(1,1,smub.nvbuffer1.readings)")
                print("Current measured : ", current)
                currents.append(current)
                voltages.append(voltage)
                
            if self.event.is_set():
                print('The thread was abort.')
                break

        if channel == "Channel A":
            keithley.write("smua.source.output = smua.OUTPUT_OFF")
            keithley.write("smua.nvbuffer1.clear()") # New : Buffer remove
        else :
            keithley.write("smub.source.output = smub.OUTPUT_OFF")
            keithley.write("smub.nvbuffer1.clear()") # New : Buffer remove
        if beep == 1:
            keithley.write("beeper.beep(0.5,2000)")
        print("IV Sweep Finished..")
        
        return voltages, currents

    def measure_iv_curve_pulse(self, keithley, channel, start_voltage, stop_voltage, step_voltage, comp_currentf, comp_currentr, on_delay, off_delay):
        voltages = []
        currents = []
        beep = self.CheckVar1.get()
        if beep == 1:
            print("Beep ON")
            keithley.write("beeper.beep(0.1,2000)")
        else:
            print("Beep OFF")

        for voltage in np.arange(start_voltage, stop_voltage + step_voltage, step_voltage):

            if channel == "Channel A":
                if voltage < 0:
                    keithley.write("smua.source.limiti = " + str(comp_currentr))
                else:
                    keithley.write("smua.source.limiti = " + str(comp_currentf))
                keithley.write("smua.source.levelv = " + str(voltage))
                keithley.write("smua.source.output = smua.OUTPUT_ON")
                time.sleep(float(on_delay) / 1000)
                keithley.write("smua.measure.i(smua.nvbuffer1)")
                current = keithley.query("printbuffer(1,1,smua.nvbuffer1.readings)")
                print("Current measured : ", current)
                currents.append(current)
                voltages.append(voltage)
                keithley.write("smua.source.output = smua.OUTPUT_OFF")
                time.sleep(float(off_delay))
            else:
                if voltage < 0 :
                    keithley.write("smub.source.limiti = " + str(comp_currentr))

                else :
                    keithley.write("smub.source.limiti = " + str(comp_currentf))
                keithley.write("smub.source.levelv = " + str(voltage))
                keithley.write("smub.source.output = smub.OUTPUT_ON")
                time.sleep(float(on_delay) / 1000)
                keithley.write("smub.measure.i(smub.nvbuffer1)")
                current = keithley.query("printbuffer(1,1,smub.nvbuffer1.readings)")
                print("Current measured : ", current)
                currents.append(current)
                voltages.append(voltage)
                keithley.write("smub.source.output = smub.OUTPUT_OFF")
                time.sleep(float(off_delay))

            if self.event.is_set():
                print('The thread was abort.')
                break

        if channel == "Channel A":
            keithley.write("smua.nvbuffer1.clear()") # New : Buffer remove
            keithley.write("smua.source.output = smua.OUTPUT_OFF")
        else :
            keithley.write("smub.nvbuffer1.clear()") # New : Buffer remove
            keithley.write("smub.source.output = smub.OUTPUT_OFF")

        if beep == 1:
            keithley.write("beeper.beep(0.5,2000)")
        print("IV Sweep Finished..")
        return voltages, currents

if __name__ == "__main__":
    root = tk.Tk()
    notebook = ttk.Notebook(root)

    notebook.pack(expand=1, fill='both')

    tab1 = VISweep(notebook)
    notebook.add(tab1, text='VI Sweep (Voltage Source)')    
    # app = IVSweep(root)
    root.mainloop()