from BaseSweep import BaseSweep
import time
import numpy as np
import os
import pandas as pd

class IVSweep(BaseSweep):
    def __init__(self, master, main_window=None):
        config = {
            "source_type": "Current source",
            "config_file": "Auto_Config_CSource.csv",
            "param_header": "Current Source Parameter",
            "start_label": "Start Current (mA):",
            "start_default": "-1",
            "stop_label": "Stop Current (mA):",
            "stop_default": "3",
            "step_label": "Step (mA):",
            "fwd_limit_label": "Forward Limit (V):",
            "rev_limit_label": "Reverse Limit (V):",
            "measure_range_label": "Measure range (V):",
            "plot_title": "IV Curve (mA-V)",
            "plot_xlabel": "Current (mA)",
            "plot_ylabel": "Voltage (V)",
        }
        super().__init__(master, main_window, config)

    def start_measurement(self):
        if os.path.isfile(os.getcwd() + "/Output/tmp_del.csv"):
            os.remove(os.getcwd() + "/Output/tmp_del.csv")
        
        self.button_abort['state'] = 'normal'
        print("Start IV Sweep.... ")
        start = time.time()
        
        interface_address = self.entry_interface.get()
        autorange_selected = self.combo_autorange.get()
        selected_type = self.combo_sweep_type.get()
        start_current = float(self.entry_start.get())
        stop_current = float(self.entry_stop.get())
        step_current = float(self.entry_step.get())
        comp_voltagef = float(self.entry_compliacncef.get())
        comp_voltager = float(self.entry_compliacncer.get())
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
        
        start_current /= 1000
        stop_current /= 1000
        step_current /= 1000

        keithley = None
        try:
            if self.combo_interface.get() == "GPIB":
                keithley = self.rm.open_resource(f'GPIB::{interface_address}::INSTR')
            elif self.combo_interface.get() == "Serial Interface":
                keithley = self.rm.open_resource(interface_address)
        except Exception as e:
            print(f"Connection failed: {e}")
            self.button_abort['state'] = 'disabled'
            return

        if off_delay == "":
            off_delay = "nan"
        else:
            off_delay = float(off_delay) / 1000

        selected_sensemode = 0 if selected_sensemode == "2-wire (Local)" else 1
        autozero = f"AUTOZERO_{autozero.upper()}"

        if selected_type == "Staircase":
            off_delay = "nan"
        elif selected_type == "Pulse":
            off_delay = float(self.entry_off_delay.get())

        if autorange_selected == "Off":
            mrange = float(self.entry_range.get())
            autorange = 0
        else:
            mrange = "nan"
            autorange = 1 if autorange_selected == "On" else 2

        print('Initialize ... ')
        self.setup_measurement(keithley, selected_channel, selected_sensemode, nplc, autozero, autorange, mrange)

        if selected_type == "Staircase":
            voltages, currents = self.measure_iv_curve_staircase(keithley, selected_channel, start_current, stop_current, step_current, comp_voltagef, comp_voltager, on_delay)
        elif selected_type == "Pulse":
            voltages, currents = self.measure_iv_curve_pulse(keithley, selected_channel, start_current, stop_current, step_current, comp_voltagef, comp_voltager, on_delay, off_delay)
        currents_mA = [float(x) * 1000 for x in currents]
        voltages_abs = [abs(float(x)) for x in voltages]

        # current_abs_A = [abs(float(x)) for x in currents]
        # current_abs_mA = [float(x) * 1000 for x in current_abs_A]
        N_measure = len(voltages)
        end = time.time()
        elapsed_time = end - start 
        print("Elapsed Time : %f s" % elapsed_time + "\n")

        df_new_data = pd.DataFrame({
            "Sourcetype" : [self.sourcetype]* N_measure, 
            "SerialNumber": [module_SN] * N_measure, 
            "Measurement_type": [measurementType] * N_measure, 
            "Channel": [selected_channel] * N_measure,
            "Sense_mode": [selected_sensemode] * N_measure, 
            "Sweep_Type": [selected_type] * N_measure, 
            "Forward_Limit(V)": [float(comp_voltagef)] * N_measure,
            "Reverse_Limit(V)": [float(comp_voltager)] * N_measure, 
            "Hold_On_Delay(ms)": [on_delay] * N_measure, 
            "Pulse_Off_Time(ms)": [off_delay] * N_measure,
            "Autorange": [autorange_selected] * N_measure, 
            "Measure_Range(V)": [mrange if mrange != 'nan' else 'nan'] * N_measure, 
            "Autozero": [autozero] * N_measure,
            "Pin": [probe_point] * N_measure, 
            "Voltage[V]": voltages_abs, 
            "Current[A]": currents, 
            "Current[mA]": currents_mA, 
            "NPLC": [nplc] * N_measure
        })

        if not os.path.exists(result_path):
            print(f"No File found... Create a new one : {filename}.csv")
            df_new_data["Label"] = 1
            df_result = df_new_data
        else:
            print(f"{filename}.csv already exists .. Overwrite the result on it")
            df = pd.read_csv(result_path)
            max_label = df['Label'].max()
            df_new_data["Label"] = max_label + 1
            df_result = pd.concat([df, df_new_data], axis=0)
        
        df_result.to_csv(result_path, index=False)
        df_new_data.to_csv(tmp_del_path, index=False)

        self.plot()
        print("IV measurement finished and saved successfully")
        print("##############################################################")
        self.button_abort['state'] = 'disabled'
        keithley.close()

    def setup_measurement(self, keithley, channel, sensemode, nplc, autozero, autorange, mrange):
        smu = "smua" if channel == "Channel A" else "smub"
        display_screen = "0" if channel == "Channel A" else "1"
        print(f"Init SMU {channel} ... ")

        keithley.write(f"{smu}.reset()")
        keithley.write(f"display.screen = {display_screen}")
        keithley.write(f"{smu}.sense = {sensemode}")
        keithley.write(f"{smu}.source.func = {smu}.OUTPUT_DCAMPS")
        keithley.write(f"{smu}.source.autorangei = 1")

        if str(autorange) == "0":
            keithley.write(f"{smu}.measure.autorangev = 0")
            keithley.write(f"{smu}.measure.rangev = {mrange}")
        else:
            keithley.write(f"{smu}.measure.autorangev = {autorange}")

        keithley.write(f"{smu}.measure.autozero = {smu}.{autozero}")
        keithley.write(f"{smu}.measure.interval = 0")
        keithley.write(f"{smu}.measure.count = 1")
        keithley.write(f"{smu}.source.delay = {smu}.DELAY_OFF")
        keithley.write(f"{smu}.measure.delay = {smu}.DELAY_OFF")
        keithley.write(f"display.{smu}.measure.func = display.MEASURE_DCVOLTS")
        keithley.write(f"{smu}.measure.nplc = {nplc}")
        print("Init SMU finished..")

    def measure_iv_curve_staircase(self, keithley, channel, start_current, stop_current, step_current, comp_voltagef, comp_voltager, on_delay):
        voltages = []
        currents = []
        smu = "smua" if channel == "Channel A" else "smub"
        beep = self.CheckVar1.get()
        if beep == 1:
            keithley.write("beeper.beep(0.1,2000)")

        for current in np.arange(start_current, stop_current + step_current, step_current):
            if self.event.is_set():
                print('The thread was aborted.')
                break

            limit = comp_voltager if current < 0 else comp_voltagef
            keithley.write(f"{smu}.source.limitv = {limit}")
            keithley.write(f"{smu}.source.leveli = {current}")
            keithley.write(f"{smu}.source.output = {smu}.OUTPUT_ON")
            time.sleep(float(on_delay) / 1000)
            keithley.write(f"{smu}.measure.v({smu}.nvbuffer1)")
            voltage = keithley.query(f"printbuffer(1,1,{smu}.nvbuffer1.readings)")
            currents.append(current)
            voltages.append(voltage)

        keithley.write(f"{smu}.source.output = {smu}.OUTPUT_OFF")
        keithley.write(f"{smu}.nvbuffer1.clear()")
        if beep == 1:
            keithley.write("beeper.beep(0.5,2000)")
        print("IV Sweep Finished..")
        return voltages, currents

    def measure_iv_curve_pulse(self, keithley, channel, start_current, stop_current, step_current, comp_voltagef, comp_voltager, on_delay, off_delay):
        voltages = []
        currents = []
        smu = "smua" if channel == "Channel A" else "smub"
        beep = self.CheckVar1.get()
        if beep == 1:
            keithley.write("beeper.beep(0.1,2000)")

        for current in np.arange(start_current, stop_current + step_current, step_current):
            if self.event.is_set():
                print('The thread was aborted.')
                break

            limit = comp_voltager if current < 0 else comp_voltagef
            keithley.write(f"{smu}.source.limitv = {limit}")
            keithley.write(f"{smu}.source.leveli = {current}")
            keithley.write(f"{smu}.source.output = {smu}.OUTPUT_ON")
            time.sleep(float(on_delay) / 1000)
            keithley.write(f"{smu}.measure.v({smu}.nvbuffer1)")
            voltage = keithley.query(f"printbuffer(1,1,{smu}.nvbuffer1.readings)")
            currents.append(current)
            voltages.append(voltage)
            keithley.write(f"{smu}.source.output = {smu}.OUTPUT_OFF")
            time.sleep(float(off_delay))

        keithley.write(f"{smu}.nvbuffer1.clear()")
        keithley.write(f"{smu}.source.output = {smu}.OUTPUT_OFF")
        if beep == 1:
            keithley.write("beeper.beep(0.5,2000)")
        print("IV Pulse Sweep Finished..")
        return voltages, currents
