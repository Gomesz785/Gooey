'''
Created on Jan 1, 2014

@author: Chris

TODO: 
	Sanitize all GetValue inputs 
	(to check that there's actual data there. 
'''

import wx
from argparse import ArgumentParser
from abc import ABCMeta, abstractmethod


class BuildException(RuntimeError):
	pass 


class AbstractComponent(object):
	'''
	Template pattern-y abstract class for the components. 
	Children must all implement the BuildWidget and getValue 
	methods. 
	'''
	__metaclass__ = ABCMeta
	
	def __init__(self):
		self._widget = None
	
	def Build(self, parent):
		
		self._widget = self.BuildWidget(parent, self._action)
		self._msg    = (self.CreateHelpMsgWidget(parent, self._action) 
										if self.HasHelpMsg(self._action) 
										else None)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.CreateDestNameWidget(parent, self._action))
		sizer.AddSpacer(2)
				
		if self._msg:
			sizer.Add(self._msg, 0, wx.EXPAND)
			sizer.AddSpacer(2)
		else:
			sizer.AddStretchSpacer(1)
			
		if self.HasNargs(self._action):
			sizer.Add(self.AddNargsMsg(parent, self._action))
		
		sizer.AddStretchSpacer(1)	
		sizer.Add(self._widget, 0, wx.EXPAND)
		return sizer
		
	def HasHelpMsg(self, action):
		return action.help is not None
	
	def HasNargs(self, action):
		return action.nargs == '+'
	
	def CreateHelpMsgWidget(self, parent, action):
		text = wx.StaticText(parent, label=action.help)
		self.MakeDarkGrey(text)
		return text
	
	def AddNargsMsg(self, parent, action):
		msg = 'Note: at least 1 or more arguments are required'
		return wx.StaticText(parent, label=msg)
	
	def CreateDestNameWidget(self, parent, action):
		label = str(action.dest).title() 
		if len(action.option_strings) > 1: 
			label += ' (%s)' % action.option_strings[0]
		text = wx.StaticText(parent, label=label)
		self.MakeBold(text)
		return text
	
	def AssertInitialization(self, clsname):
		if not self._widget:
			raise BuildException('%s was not correctly initialized' % clsname)
		
	def MakeBold(self, statictext):
		pointsize = statictext.GetFont().GetPointSize()
		statictext.SetFont(wx.Font(pointsize, wx.FONTFAMILY_DEFAULT,
				wx.FONTWEIGHT_NORMAL, wx.FONTWEIGHT_BOLD, False))
		
	def MakeDarkGrey(self, statictext):
		darkgray = (54,54,54)
		statictext.SetForegroundColour(darkgray)
		
	def __str__(self):
		return str(self._action)
		
	@abstractmethod
	def BuildWidget(self, parent, action):
		''' Must construct the main widget type for the Action '''
		pass
	
	@abstractmethod
	def GetValue(self):
		''' Returns the state of the given widget '''
		pass
	
# 	@abstractmethod
	def Update(self, size):
		''' 
		Manually word wraps the StaticText help objects which would 
		otherwise not wrap on resize
		
		Content area is based on each grid having two equally sized 
		columns, where the content area is defined as 87% of the halved
		window width. The wiggle room is the distance +- 10% of the 
		content_area. 
		
		Wrap calculation is run only when the size of the help_msg 
		extends outside of the wiggle_room. This was done to avoid 
		the "flickering" that comes from constantly resizing a 
		StaticText object.     
		'''
		if self._msg is None: 
			return
		help_msg = self._msg
		width, height = size
		content_area = int((width/2)*.87)

		print 'wiget size', help_msg.Size[0]
		wiggle_room = range(int(content_area - content_area * .05), int(content_area + content_area * .05))
		print '(',int(content_area - content_area * .05), int(content_area + content_area * .05),')'
		if help_msg.Size[0] not in wiggle_room:
				self._msg.SetLabel(self._msg.GetLabelText().replace('\n',' '))
				self._msg.Wrap(content_area)
		



class Positional(AbstractComponent):
	def __init__(self, action):
		self._action = action
		self._widget = None
		self.contents = None
	
	def BuildWidget(self, parent, action):
		return wx.TextCtrl(parent)
	
	def GetValue(self):
		'''
		Positionals have no associated options_string, 
		so only the supplied arguments are returned. 
		The order is assumed to be the same as the order 
		of declaration in the client code
		
		Returns
			"argument_value"
		'''
		self.AssertInitialization('Positional')
		return self._widget.GetValue()

	
class Choice(AbstractComponent):
	_DEFAULT_VALUE = 'Select Option'
	def __init__(self, action):
		self._action = action
		self._widget = None
		self.contents = None 
		
	def GetValue(self):
		'''
		Returns
			"--option_name argument"
		'''
		self.AssertInitialization('Choice')
		if self._widget.GetValue() == self._DEFAULT_VALUE:
			return ''
		return ' '.join(
									[self._action.option_strings[-1], # get the verbose copy if available  
									self._widget.GetValue()])
	
	def BuildWidget(self, parent, action):
		return wx.ComboBox(
							parent=parent,
							id=-1,
							value=self._DEFAULT_VALUE,
							choices=action.choices, 
							style=wx.CB_DROPDOWN
							) 
	

class Optional(AbstractComponent):
	def __init__(self, action):
		self._action = action
		self._widget = None
		self.contents = None 
		
	def BuildWidget(self, parent, action):
		return wx.TextCtrl(parent)
	
	def GetValue(self):
		'''
		General options are key/value style pairs (conceptually). 
		Thus the name of the option, as well as the argument to it 
		are returned
		e.g. 
			>>> myscript --outfile myfile.txt
		returns 
			"--Option Value" 
		'''
		self.AssertInitialization('Optional')
		return ' '.join(
							[self._action.option_strings[-1], # get the verbose copy if available  
							self._widget.GetValue()])
		

class Flag(AbstractComponent):
	def __init__(self, action):
		self._action = action
		self._widget = None
		self.contents = None
		
	def Build(self, parent):
		self._widget = self.BuildWidget(parent, self._action)
		self._msg    = (self.CreateHelpMsgWidget(parent, self._action) 
										if self.HasHelpMsg(self._action) 
										else None)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.CreateDestNameWidget(parent, self._action))
		sizer.AddSpacer(6)
				
		if self.HasNargs(self._action):
			sizer.Add(self.AddNargsMsg(parent, self._action))
			
		if self._msg: 
			hsizer = self.buildHorizonalMsgSizer(parent)
			sizer.Add(hsizer, 1, wx.EXPAND)
		else:
			sizer.AddStretchSpacer(1)	
			sizer.Add(self._widget, 0, wx.EXPAND)
		return sizer
		
	def BuildWidget(self, parent, action):
		return wx.CheckBox(parent, -1, label='')
	
	def buildHorizonalMsgSizer(self, panel):
		if not self._msg:
			return None
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self._widget, 0)
		sizer.AddSpacer(6)
		sizer.Add(self._msg, 1, wx.EXPAND)
		return sizer
		
	def GetValue(self):
		'''
		Flag options have no param associated with them. 
		Thus we only need the name of the option. 
		e.g 
			>>> Python -v myscript
		returns 
			Options name for argument (-v)
		'''
		return self._action.option_strings[-1]
	
	def Update(self, size):
		''' 
		Custom wrapper calculator to account for the
		increased size of the _msg widget after being 
		inlined with the wx.CheckBox
		''' 
		if self._msg is None: 
			return
		help_msg = self._msg
		width, height = size
		content_area = int((width/3)*.70)

		print 'wiget size', help_msg.Size[0]
		wiggle_room = range(int(content_area - content_area * .05), int(content_area + content_area * .05))
		print '(',int(content_area - content_area * .05), int(content_area + content_area * .05),')'
		if help_msg.Size[0] not in wiggle_room:
				self._msg.SetLabel(self._msg.GetLabelText().replace('\n',' '))
				self._msg.Wrap(content_area)
	
	
	
class Counter(AbstractComponent):
	def __init__(self, action):
		self._action = action
		self._widget = None
		self.contents = None
		
	def BuildWidget(self, parent, action):
		levels = [str(x) for x in range(1, 7)]
		return wx.ComboBox(
							parent=parent,
							id=-1,
							value='',
							choices=levels, 
							style=wx.CB_DROPDOWN
							) 
		
	def GetValue(self):
		'''
		NOTE: Added on plane. Cannot remember exact implementation 
		of counter objects. I believe that they count sequentail 
		pairings of options
		e.g. 
			-vvvvv 
		But I'm not sure. That's what I'm going with for now.
		
		Returns 
			str(action.options_string[0]) * DropDown Value
		'''
		dropdown_value = self._widget.GetValue()
		try: 
			return str(self._action.option_strings[0]) * int(dropdown_value) 
		except Exception as e:
			print e 
			return '' 
		
		
		

if __name__ == '__main__':
	pass

	
		
		
		
		