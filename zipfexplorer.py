from collections import defaultdict
from collections import OrderedDict
import random

from nltk.tokenize import RegexpTokenizer
import powerlaw

from scipy import stats
from scipy.stats import kstest
import numpy as np

import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import argparse
import sys
import os
import glob
import csv

from Tkinter import *
import tkFileDialog as tkf
import tkSimpleDialog as tksd
import tkMessageBox
import ttk

class mainWindow(Tk):
	def __init__(self):
		Tk.__init__(self)

		self.title("Zipf Explorer")
		self.option_add('*tearOff', FALSE) #screw you tear off menus FUCK YOU
		ico = PhotoImage(file='icon.gif')
		self.tk.call('wm', 'iconphoto', self._w, ico)

		self.tabMan = tabManager(self)
		self.tokenLimit = 0

		menu = Menu(self)
		self.config(menu=menu)

		filemenu = Menu(menu)
		menu.add_cascade(label="File", menu=filemenu)
		filemenu.add_command(label="Open...", underline = 0, accelerator="Ctrl+O", command=lambda: self.openText(None))
		filemenu.add_command(label="Limit Token Amount...", command = self.limitDialogueCallBack)
		filemenu.add_command(label="Save Single Result As...", underline = 0, accelerator="Ctrl+S", command = lambda: self.saveSingleResult(None))
		filemenu.add_separator()
		filemenu.add_command(label="Close Tab", underline = 0, accelerator="Ctrl+C", command=lambda: self.closeTabCallBack(None))
		filemenu.add_command(label="Quit", underline = 0, accelerator="Ctrl+Q", command= lambda: self.exitCallBack(None))
		self.bind_all("<Control-q>", self.exitCallBack)
		self.bind_all("<Control-o>", self.openText)
		self.bind_all("<Control-s>", self.saveSingleResult)
		self.bind_all("<Control-c>", self.closeTabCallBack)


		processmenu = Menu(menu)
		menu.add_cascade(label = "Process", menu=processmenu)
		processmenu.add_command(label = "Frequency Table", underline = 9, accelerator="Ctrl+T", command = lambda: self.freqTableCallBack(None)) #so this should make tabs happen OK?
		processmenu.add_command(label = "Plot", underline = 0, accelerator="Ctrl+P", command = lambda: self.plotCallBack(None))
		processmenu.add_command(label = "Fit values", underline = 0, accelerator="Ctrl+F", command = lambda: self.fitValuesCallBack(None))
		self.bind_all("<Control-t>", self.freqTableCallBack)
		self.bind_all("<Control-p>", self.plotCallBack)
		self.bind_all("<Control-f>", self.fitValuesCallBack)

		batchmenu = Menu(menu)
		menu.add_cascade(label = "Batch", menu=batchmenu)
		batchmenu.add_command(label = "Generate Report", underline = 10, accelerator="Ctrl+R", command = lambda: self.reportCallBack(None))
		self.bind_all("<Control-r>", self.reportCallBack)

		helpmenu = Menu(menu)
		menu.add_cascade(label="Help", menu=helpmenu)
		helpmenu.add_command(label="About...", command=self.aboutBox)

	def aboutBox(self):
		tkMessageBox.showinfo("About", "Zipf Explorer | cmessner.com")

	def exitCallBack(self, event):
		self.destroy()
		sys.exit(0)

####save functions###

	def limitDialogueCallBack(self):
		self.tokenLimit = tksd.askinteger("Token Limit?", "Limit texts to the first (0 means no limit):")

	def reportCallBack(self, event):
		self.tabMan.saveReport()

	def saveSingleResult(self, event):
		self.tabMan.saveSingle(self.tabMan.tab(self.tabMan.select(), "text"))

	### these all pass the name of the currently focused on tab to the manager
	def freqTableCallBack(self, event):
		self.tabMan.dispTable(self.tabMan.tab(self.tabMan.select(), "text")) #the freqtable menu item passes the current tab to the tab manager

	def fitValuesCallBack(self, event):
		self.tabMan.dispFit(self.tabMan.tab(self.tabMan.select(), "text")) #the freqtable menu item passes the current tab to the tab manager

	def plotCallBack(self, event):
		self.tabMan.dispPlot(self.tabMan.tab(self.tabMan.select(), "text"))

	def closeTabCallBack(self, event):
		self.tabMan.closeTab(self.tabMan.tab(self.tabMan.select(), "text"))

		#####

	def openText(self, event):
		#totalText = []
		outRow = []

		frequencies = defaultdict(int)

		tokenizer = RegexpTokenizer("[\w']+") #improve -- taking 'a' as a diff token from a but needs to retain contraction support
		
		#multiple files
		try:
			files = tkf.askopenfilenames()
			

		except IOError:
			print "Cancel/File not Found"
			return

		files = root.splitlist(files)
		for infile in files:
			with open(infile, 'r') as fileName:
				for line in fileName: 
					for word in tokenizer.tokenize(line):
						word = unicode(word, 'ascii', 'ignore')
						if word and word[0] == '\'' and word[:1] == '\'': # a stupid crutch to remove the overinclusive end ''s left by tokenizer
							word = word[1:-1]
						if word: #no blanks!
							if self.tokenLimit == 0 or sum(frequencies.values()) < self.tokenLimit: #if there is no token limit or we are below the specified token limit
								frequencies[word.lower()] += 1
							

							#totalText.append(word.lower()) #maintain words in order for monkey things
				#outRow.append(fileName.name.split('/')[-1]) #for the actual display just save the .txt filename, not the whole path
				fileName.close()



			orderedKeys = sorted(frequencies, key = frequencies.get, reverse = True)
			orderedFreq = OrderedDict(zip(orderedKeys, [frequencies[x] for x in orderedKeys])) #keys, frequencies of words by descending frequency 


			self.tabMan.addText(fileName.name.split('/')[-1], orderedFreq)




class tabManager(ttk.Notebook): #checking that we have only one tab open for each file here, etc.
	def __init__(self, parent):
		 ttk.Notebook.__init__(self, parent, width=640, height = 480)
		 self.pack(fill='both', expand=1) 

		 self.tabDict = {}
		 self.enable_traversal()


	def addText(self, name, freq): #load a text from file into the dictionary
		self.tabDict[name] = tabView(self, name, freq)
		self.tabDict[name].freqTabView()
		for openTab in self.tabs(): #these three lines just make it so that focus automatically switches to a newly-opened tab
			if self.tab(openTab, "text") == name:
				self.select(openTab)

	def dispTable(self, name):
		if name in self.tabDict:
			self.tabDict[name].freqTabView()

	def dispFit(self, name):
		if name in self.tabDict:
			self.tabDict[name].fitDataView()

	def dispPlot(self, name):
		if name in self.tabDict:
			self.tabDict[name].plotView()


	def closeTab(self, name): #remove from dictionary and forget tab
		if name in self.tabDict:
			self.tabDict[name].destroy()
			self.tabDict.pop(name)
			

	def saveReport(self):
		try:
			with tkf.asksaveasfile(mode='w', defaultextension=".csv") as of:
				for key in self.tabDict:
					of.write(','.join(self.tabDict[key].fitDataView()) + '\n') #process every open tab
			of.close()
		except AttributeError:
			print "Cancel/File not Found"
			return

	def saveSingle(self, name):
		if name in self.tabDict:
			with tkf.asksaveasfile(mode='w', defaultextension=".csv") as of:
				for item in self.tabDict[name].orderedFreq:
					of.write(item + "," + str(self.tabDict[name].orderedFreq[item]) +'\n')
		


class tabView(Frame):
	def __init__(self, parent, nameText, orderedFreq):
		Frame.__init__(self, parent)

		parent.add(self, text=nameText)
		self.outRow = [nameText]
		self.orderedFreq = orderedFreq
		self.outRowHeadings = ["Text", "Total Tokens", "Alpha", "vs. Exponential Liklihood", "vs. Exponential Pvalue", "vs. Lognormal Liklihood", "vs. Lognormal Pvalue"]


	def freqTabView(self):

		self.clearView()

		textDisplay = Canvas(self, width=200, height=480) 
		textDisplay.pack(fill=BOTH, expand=YES, side = LEFT)

		vbar=Scrollbar(self, orient=VERTICAL)  #TODO, mouse wheel
		vbar.pack(side=RIGHT, fill = Y, expand = FALSE)
		vbar.config(command=textDisplay.yview)
		


		y = 12
		for key, value in self.orderedFreq.items():
			textDisplay.create_text(10,y, text = key, justify = "center", anchor = "nw") #lines bewtween rows?
			textDisplay.create_text(140,y, text = value, justify = "center", anchor = "nw")
			textDisplay.create_line(0, y+14, textDisplay.winfo_reqwidth(), y+14) 
			y+=22
	
		textDisplay.config(yscrollcommand=vbar.set, scrollregion = textDisplay.bbox("all"))

		return self.orderedFreq

	def fitDataView(self):

		self.clearView()

		total = sum(self.orderedFreq.values())
		self.outRow.append(str(total))  #total amount of words

		results = powerlaw.Fit(self.orderedFreq.values(), discrete=True) #fit to powerlaw distribution
	
		self.outRow.append(str(results.power_law.alpha)) #alpha

		R, p = results.distribution_compare('power_law', 'exponential',  normalized_ratio=True)
		#print "Liklihood for power instead of exponential, P-value"
		#print R, p
		self.outRow.append(str(R))
		self.outRow.append(str(p))


		R, p = results.distribution_compare('power_law', 'lognormal',  normalized_ratio=True)
		#print "Liklihood for power instead of lognormal, P-value"
		#print R, p
		self.outRow.append(str(R))
		self.outRow.append(str(p))


		textDisplay = Canvas(self, width = 800, height = 100)
		textDisplay.pack(fill=BOTH, expand=YES)
		
	
		x = 0
		for heading in self.outRowHeadings:
			textDisplay.create_text(10+x, 10, text=heading, anchor="nw")
			x += 200
		
		textDisplay.create_line(0, 25, 175*len(self.outRowHeadings)+10, 25)
		
		x = 0
		for info in self.outRow:
			textDisplay.create_text(10+x, 35, text = info, anchor = "nw")
			x+=200

		hbar=Scrollbar(self,orient=HORIZONTAL)
		hbar.pack(side=BOTTOM, fill = Y, expand = FALSE)
		hbar.config(command=textDisplay.xview)
		

		textDisplay.config(xscrollcommand=hbar.set, scrollregion = textDisplay.bbox("all"))

		return self.outRow



	def plotView(self):
		self.clearView()

		f = Figure(figsize=(5,4), dpi=100)
		a = f.add_subplot(111)
		test = powerlaw.plot_ccdf(self.orderedFreq.values(), ax = a, color = 'b')
		a.plot()
	
		canvas = FigureCanvasTkAgg(f, master=self)
		canvas.show()
		canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)


		toolbar = NavigationToolbar2TkAgg( canvas, self )
		toolbar.update()
		canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)



	def clearView(self): 
		for child in self.winfo_children():
			child.destroy()







if __name__ == "__main__":

	root = mainWindow()

	root.mainloop()