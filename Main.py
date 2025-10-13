from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from VI_Sweep import VISweep
from IV_Sweep import IVSweep


Version = "V5_tmp (251013)"

print("##############################################################")
print(f"Version : {Version}")
print("##############################################################")



def main():
 

    global window 
    window = Tk()


    notebook = ttk.Notebook(window)

    notebook.pack(expand=1, fill='both')

    tab1 = VISweep(notebook)
    tab2 = IVSweep(notebook)



    notebook.add(tab1, text='VI Sweep (Voltage Source)')
    notebook.add(tab2, text='IV Sweep (Current Source)')

    #Main loop
    window.mainloop()

if __name__ == '__main__':
    main()