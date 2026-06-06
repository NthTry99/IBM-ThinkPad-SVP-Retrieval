import tkinter as tk
from ibmSVP_scanDecoder.gui import DecoderAPP

if __name__ == "__main__":
    root = tk.Tk()
    app = DecoderAPP(root)
    root.mainloop()