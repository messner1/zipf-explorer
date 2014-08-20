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
import tkMessageBox
import ttk


orderedFreq = {}
outRow = []


def openText(event):

	global outRow
	global orderedFreq
	global totalText


	totalText = []
	outRow = []

	frequencies = defaultdict(int)
	

	tokenizer = RegexpTokenizer("[\w']+") #improve -- taking 'a' as a diff token from a but needs to retain contraction support
	
	try:
		with open(tkf.askopenfilename(), 'r') as fileName:
			for line in fileName: 
				for word in tokenizer.tokenize(line):
					frequencies[word.lower()] += 1
					totalText.append(word.lower()) #maintain words in order for monkey things
			outRow.append(fileName.name.split('/')[-1]) #for the actual display just save the .txt filename, not the whole path
			fileName.close()
	except IOError:
		print "Cancel/File not Found"
		return

	orderedKeys = sorted(frequencies, key = frequencies.get, reverse = True)
	orderedFreq = OrderedDict(zip(orderedKeys, [frequencies[x] for x in orderedKeys])) #keys, frequencies of words by descending frequency 

	root.title("Zipf Explorer - " + fileName.name)
	dispFreqTable(event)

def saveSingleResult(event):
	if len(outRow) < 2: #if the only thing in outRow is the filename (which is loaded before processing) or nothing at all
		tkMessageBox.showerror("Process Error","Load a text and run \"Fit Text\" command before saving")
		return

	try:
		with tkf.asksaveasfile(mode='w', defaultextension=".csv") as of: #append data row 
			of.write(','.join(["Text", "Total Tokens", "Alpha", "vs. Exponential Liklihood", "vs. Exponential Pvalue", "vs. Lognormal Liklihood", "vs. Lognormal Pvalue"])+'\n')
			of.write(','.join(outRow) + '\n')
			of.write('Token, Value, Frequency\n')
			for key, value in orderedFreq.items():
				of.write(key+","+str(value)+","+str(value/float(len(totalText)))+'\n')
			of.close()
	except AttributeError:
		print "Cancel/File not Found"
		return

def appendCallback(event):
	if len(outRow) < 2: #if the only thing in outRow is the filename (which is loaded before processing) or nothing at all
		tkMessageBox.showerror("Process Error","Load a text and run \"Fit Text\" command before saving")
		return

	try:
		with tkf.asksaveasfile(mode='a', defaultextension=".csv") as of:
			of.write(','.join(outRow) + '\n')
			of.close()
	except AttributeError:
		print "Cancel/File not Found"
		return
		
def deleteDisplay():
	for child in root.winfo_children():
		if not isinstance(child, Menu): #delete anything that isn't the menu to make room for the graph or the freq table or w/e
			child.destroy()

def dispFreqTable(event):

	if not orderedFreq:
		tkMessageBox.showerror("Process Error","Load a .txt file first")
		return

	deleteDisplay()


	frame=Frame(root,width=200,height=480) #scrollbar on this
	frame.pack(fill=BOTH, expand=YES)	

	textDisplay = Canvas(frame, width=200, height=480) #last restricts scrolling area
	textDisplay.pack(fill=BOTH, expand=YES, side = LEFT)
	

	vbar=Scrollbar(frame, orient=VERTICAL)
	vbar.pack(side=RIGHT, fill = Y, expand = FALSE)
	vbar.config(command=textDisplay.yview)
	

	
	textDisplay.update_idletasks() #gotta do for winfo_width to work (pack doesn't actually manage geo)


	y = 12
	for key, value in orderedFreq.items():
		textDisplay.create_text(10,y, text = key, justify = "center", anchor = "nw") #lines bewtween rows?
		textDisplay.create_text(100,y, text = value, justify = "center", anchor = "nw")
		textDisplay.create_line(0, y+14, textDisplay.winfo_width(), y+14)
		y+=22
	
	textDisplay.config(yscrollcommand=vbar.set, scrollregion = textDisplay.bbox("all"))

def dispFitData(event):

	if not orderedFreq:
		tkMessageBox.showerror("Process Error","Load a .txt file first")
		return


	deleteDisplay()
	total = sum(orderedFreq.values())
	outRow.append(str(total))  #total amount of words

	results = powerlaw.Fit(orderedFreq.values(), discrete=True) #fit to powerlaw distribution
	
	outRow.append(str(results.power_law.alpha)) #alpha

	R, p = results.distribution_compare('power_law', 'exponential',  normalized_ratio=True)
	#print "Liklihood for power instead of exponential, P-value"
	#print R, p
	outRow.append(str(R))
	outRow.append(str(p))


	R, p = results.distribution_compare('power_law', 'lognormal',  normalized_ratio=True)
	#print "Liklihood for power instead of lognormal, P-value"
	#print R, p
	outRow.append(str(R))
	outRow.append(str(p))

	frame = Frame(root, width = 800, height = 100)
	frame.pack(fill = BOTH, expand = YES)

	textDisplay = Canvas(frame, width = 800, height = 100)
	textDisplay.pack(fill=BOTH, expand=YES)
	
	outRowHeadings = ["Text", "Total Tokens", "Alpha", "vs. Exponential Liklihood", "vs. Exponential Pvalue", "vs. Lognormal Liklihood", "vs. Lognormal Pvalue"]
	x = 0
	for heading in outRowHeadings:
		textDisplay.create_text(10+x, 10, text=heading, anchor="nw")
		x += 175
	
	textDisplay.create_line(0, 25, 175*len(outRowHeadings)+10, 25)
	
	x = 0
	for info in outRow:
		textDisplay.create_text(10+x, 35, text = info, anchor = "nw")
		x+=175

	hbar=Scrollbar(frame,orient=HORIZONTAL)
	hbar.pack(side=BOTTOM, fill = Y, expand = FALSE)
	hbar.config(command=textDisplay.xview)
	

	textDisplay.config(xscrollcommand=hbar.set, scrollregion = textDisplay.bbox("all"))

def plotCallback(event):

	if not orderedFreq:
		tkMessageBox.showerror("Process Error","Load a .txt file first")
		return


	deleteDisplay()

	f = Figure(figsize=(5,4), dpi=100)
	a = f.add_subplot(111)
	test = powerlaw.plot_ccdf(orderedFreq.values(), ax = a, color = 'b')
	a.plot()
	
	canvas = FigureCanvasTkAgg(f, master=root)
	canvas.show()
	canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)


	toolbar = NavigationToolbar2TkAgg( canvas, root )
	toolbar.update()
	canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
#eventually combine command line w/ gui here -- if cl option is selected start in GUI, otherwise call functions accordingly?

if __name__ == "__main__":

	def exitCallback(event):
		root.destroy()
		sys.exit(0)

	def aboutBox():
   		tkMessageBox.showinfo("About", "Zipf Explorer | cmessner.com")



	root = Tk()
	root.title("Zipf Explorer")
	root.option_add('*tearOff', FALSE) #screw you tear off menus FUCK YOU
	

	# create a menu
	menu = Menu(root)
	root.config(menu=menu)

	filemenu = Menu(menu)
	menu.add_cascade(label="File", menu=filemenu)
	filemenu.add_command(label="Open...", underline = 0, accelerator="Ctrl+O", command=lambda: openText(None))
	filemenu.add_command(label="Save Single Result As...", underline = 0, accelerator="Ctrl+S", command = lambda: saveSingleResult(None))
	filemenu.add_command(label="Append digest to CSV...", underline = 0, accelerator="Ctrl+A", command = lambda: appendCallback(None))
	filemenu.add_separator()
	filemenu.add_command(label="Quit", underline = 0, accelerator="Ctrl+Q", command= lambda: exitCallback(None))
	root.bind_all("<Control-q>", exitCallback)
	root.bind_all("<Control-o>", openText)
	root.bind_all("<Control-s>", saveSingleResult)
	root.bind_all("<Control-a>", appendCallback)

	processmenu = Menu(menu)
	menu.add_cascade(label = "Process", menu=processmenu)
	processmenu.add_command(label = "Frequency Table", underline = 10, accelerator="Ctrl+T", command = lambda: dispFreqTable(None)) #so this should make tabs happen OK?
	processmenu.add_command(label = "Plot", underline = 0, accelerator="Ctrl+P", command = lambda: plotCallback (None))
	processmenu.add_command(label = "Fit values", underline = 0, accelerator="Ctrl+F", command = lambda: dispFitData (None))
	root.bind_all("<Control-t>", dispFreqTable)
	root.bind_all("<Control-p>", plotCallback)
	root.bind_all("<Control-f>", dispFitData)

	helpmenu = Menu(menu)
	menu.add_cascade(label="Help", menu=helpmenu)
	helpmenu.add_command(label="About...", command=aboutBox)

	mainloop()

	#parser = argparse.ArgumentParser(description='Use power laws to explore text')
	#parser.add_argument('-i', '--infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help = 'Filename for a single input file')
	#parser.add_argument('-d', '--indirectory', nargs=1, type=str,  help = 'Process all text files in a given directory')
	#parser.add_argument('-o', '--outdirectory', nargs=1, type=str, default = "",  help = 'Directory in which to place output files')
	#parser.add_argument('-e', '--expanded', action='store_true', help = 'Produce expanded reports for each input file')

	#args = parser.parse_args()


	#with open(args.outdirectory + 'powerdigest.csv', 'w') as of:
	#	of.write('Filename, Total Tokens, Power Fit Alpha, vs. Exponential Likelihood, vs. Exponential P-value, vs. Lognormal Liklihood, vs. Lognormal P-value\n')

	#if args.indirectory: #if a directory was given
	#	for filename in glob.glob(os.path.join(args.indirectory[0], '*.txt')):	#get all the .txt files in directory
	#		processText(open(filename, 'r'), args.outdirectory, args.expanded)
	#else:
	#	processText(args.infile, args.outdirectory, args.expanded) #otherwise read the single file option, even if it is just stdin





















#################################################################MESSING AROUND #############################################################	
def monkey(freqData, text): #uses less frequent words instead of most, proportionate. Data = orderedfreq
	inversetext = ""
	flipped = defaultdict(list) 
	for freq in freqData.items():
		flipped[freq[1]].append(freq[0])
		
	print flipped

	for word in text:
		inversetext = inversetext + " " + random.choice(flipped[freqData[word]])
	return inversetext





def obtusemonkey(freqData, text): #inverts frequencies - so the words that appear most often will now appear least. Moves all that occur at a given interval to the complementary one and then selects one of those words at generation time
	obtusetext = ""
	
	flipped = defaultdict(list) 
	for freq in freqData.items():
		flipped[freq[1]].append(freq[0])
		
	orderinverse = OrderedDict(sorted(flipped.items(), key=lambda t: t[0]))
	invert = {}
	
	keys = orderinverse.keys()
	for index in range(0, len(keys)/2):
		invert[keys[len(keys)-(index+1)]] = orderinverse[keys[index]]
		invert[keys[index]] = orderinverse[keys[len(keys)-(index+1)]]
	for key in keys: #get the potential odd one out
		if key not in invert.keys():
			invert[key] = orderinverse[key]
		
	for word in text:
		obtusetext = obtusetext + " " + random.choice(invert[freqData[word]])
		#print freqData[word], invert[freqData[word]]
	return obtusetext
	
	
def obtusermonkey(freqData, text): #same as above, but selects only one word from each frequency to generate
	obtusetext = ""
	
	flipped = defaultdict(list) 
	for freq in freqData.items():
		flipped[freq[1]].append(freq[0])
		
	orderinverse = OrderedDict(sorted(flipped.items(), key=lambda t: t[0]))
	invert = {}
	
	keys = orderinverse.keys()
	for index in range(0, len(keys)/2):
		invert[keys[len(keys)-(index+1)]] = random.choice(orderinverse[keys[index]])
		invert[keys[index]] = random.choice(orderinverse[keys[len(keys)-(index+1)]])
	for key in keys: #get the potential odd one out
		if key not in invert.keys():
			invert[key] = orderinverse[key]
		
	for word in text:
		obtusetext = obtusetext + " " + "".join(invert[freqData[word]])
		#print freqData[word], invert[freqData[word]]
	return obtusetext
	
