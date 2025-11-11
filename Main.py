from tkinter import *
from tkinter import ttk
from VI_Sweep import VISweep
from IV_Sweep import IVSweep

Version = "V5_tmp_refactored (251015)"

print("##############################################################")
print(f"Version : {Version}")
print("##############################################################")

def main():
    scale_factor = 1.0

    global window 
    window = Tk()
    window.title("IV/VI Curve Measurement")

    # 창 크기 조절 가능하도록 설정
    window.resizable(True, True)

    # 화면 크기에 맞춰 창 크기 조정
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window.geometry(f"{int(screen_width * 0.8)}x{int(screen_height * 0.8)}")
    window.minsize(1280, 720) # 창의 최소 크기 설정

    notebook = ttk.Notebook(window)
    notebook.pack(expand=1, fill='both')

    tab1 = VISweep(notebook, window)
    tab2 = IVSweep(notebook, window)

    tabs = [tab1, tab2]

    def zoom(event):
        nonlocal scale_factor
        if event.delta > 0 or event.keysym == 'plus':
            scale_factor *= 1.1
        elif event.delta < 0 or event.keysym == 'minus':
            scale_factor /= 1.1
        
        # 스케일 팩터의 최대/최소값 제한
        scale_factor = max(0.5, min(scale_factor, 2.0))

        for tab in tabs:
            if hasattr(tab, 'apply_zoom'):
                tab.apply_zoom(scale_factor)

    # Ctrl + Mouse Wheel (Windows/macOS)
    window.bind("<Control-MouseWheel>", zoom)
    # Ctrl + Plus/Minus key
    window.bind("<Control-plus>", zoom)
    window.bind("<Control-minus>", zoom)
    # for numpad
    window.bind("<Control-KP_Add>", zoom)
    window.bind("<Control-KP_Subtract>", zoom)

    notebook.add(tab1, text='VI Sweep (Voltage Source)')
    notebook.add(tab2, text='IV Sweep (Current Source)')

    window.mainloop()

if __name__ == '__main__':
    main()
