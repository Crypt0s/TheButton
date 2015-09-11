#!/usr/bin/python
from Tkinter import *
import pdb
import logging
import signal
import sys
from googlefinance import getQuotes
import json
import threading
import logging

class Stock:
    def update_ui(self):
        price = getQuotes('KEYW')[0]['LastTradeWithCurrency'] + "    "
        self.w1.config(text=price)
        # need to re-set this after it runs
        self.master.after(10000, self.update_ui)
        logging.debug("Updated stock UI")
        return True

    def __init__(self):   

        # logging setup
        logging.basicConfig(filename='/opt/button/log.log', level=logging.DEBUG)
        logging.debug('entered the stock program')

        self.master = Tk()
        self.master.title("Stockwatch")
    
        # Fullsize screen code
        w,h = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        self.master.overrideredirect(1)
        self.master.geometry("%dx%d+0+0" % (w,h))
        self.master.focus_set()
        self.master.bind("<Escape>", lambda e: e.widget.quit())
    
        # Logo and stock price
        logo = PhotoImage(file="/opt/button/keyw.gif")
        self.w1 = Label(self.master, image=logo, compound="right", text="Loading...")
        self.w1.pack(side="right")
        self.w1.config(font='Arial 60 bold')
        
        # update the quote every 10 seconds (probably overkill)
        self.master.after(10000, self.update_ui)
        mainloop()
        
    
# for testing purposes
if __name__ == "__main__":
    mystock = Stock()
