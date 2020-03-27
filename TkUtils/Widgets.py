'''This module contains all of the custom Widget/window classes'''

from tkinter import Tk, Button, IntVar, StringVar, DoubleVar, BooleanVar, Entry, Label, Widget, Toplevel, Frame, Message
from typing import Tuple, Callable, Union, List, Any, Iterable, Dict
from .factory import WidgetFactory
from ..callbacks import Callback
from ..checks import CHECKTYPES
from traceback import print_exc

class Popup:
    '''Popup class intended to be used for errors,
   but flexible enough to be used for any popup.

   NOTE
   Use .close() to close Popups manually. 
   Do not directly call _window.destroy() or it will cause an error
   next time a Popup is spawned.
   
   ATTRIBUTES
   instances: class attr. dict of the currently alive instances. 
        Format: name : instance

   _population: integer for tracking current number of instances and auto-triggering culling.
   Popups are culled every 2 open popups. If modified: the user must clean up the instances attr accordingly.
   _name: string to describe the purpose of the popup. Composite key of name+population.
   _window: the root window of the popup.
   _errorBackground: all widgets are placed on this. Destroy it to clear the popup.
   _message: Message widget that contains the input text.
   _dieButton: Button to close the widget.
   _parentPopup: Popup that will be closed when this instance closes.
   '''

    #attributes
    _population=0
    instances={}

    def __init__(self, text: str="Something went wrong", title: str="Error!", name: str=None,
        textColour: str = "red", parentPopup: 'Popup' = None):
        '''Builds a custom popup

        ARGUMENTS:
        text: (optional) the text for the message.
        Defaults to 'Something went wrong.'

        title: (optional) the window title. 
        Defaults to 'Error'

        name: the name of the instance. Used to reference the instance
        from the instances attribute and should describe the instance of the popup.
        The current population will be appended to the attribute to ensure it's unique.
        Defaults to the title plus the current population.

        textColour: the fg attribute of the label

        parentPopup: the popup to attach to. 
        It will be destroyed when this instance is destroyed.
        '''

        self._parentPopup = parentPopup

        #culling the population if too many popups are active
        if self._population>=2:
            toDelete = [list(self.instances.keys())[i] for i in range(0, 2)]

            for key in toDelete:
                del Popup.instances[key]

            Popup._population -= 2

        #create window
        self._window=Tk()
        self._window.protocol("WM_DELETE_WINDOW", self.close)  #close is called when the window is closed by user
        self._window.title(title)

        #create background
        self._errorBackground=Frame(self._window, height=200, width=200)
        self._errorBackground.grid(row=0, column=0)

        #create message
        self._message=Message(text=text, master=self._window, fg=textColour, width=120)
        self._message.place(x =100, y=75, anchor="center")

        #create dismiss button
        self._dieButton=Button(text="Dismiss", master=self._window)

        # bind the close command
        self._dieButton["command"] = self.close

        self._dieButton.place(x=100, y=125, anchor="center")

        #update population
        Popup._population+=1
        if name is not None:
            self._name=f"{name}{self._population}"  #population appended to ensure it's unique

        else:
            self._name=f"{title}{self._population}"

        Popup.instances[self._name]=self


    def close(self):
        '''Kills the window and cleans up the class data'''

        # clean up instances
        try:
            del Popup.instances[self._name]

        except KeyError:  # silence the error
            #KeyError would mean that __init__ failed before the end
            #perhaps add a status attribute
            #and log death circumstances instead of silencing this
            pass

        # handle parent
        if self._parentPopup:
            self._parentPopup.close()
            
        # finally, kill the window
        try:
            self._window.destroy()
            Popup._population -= 1

        except:
            #will result in an infinite loop if this is caused by a code error
            Popup(text="Unable to kill popup", title="Popup error!", name="Popup Error")


class ToolTip(Toplevel):
    '''Class to create tool tips when hovering over a widget.
    Supports grouping widgets under one ToolTip instance.

    ATTRIBUTES
    _widgets: list of parent widgets of the tooltip.
    _master: the master container or window of the ToolTip.
    label: the widget that displays the text.
    text: the string text of the label. Does not change.
    getText: the function that returns the text for the label on each hover.
    Allows for dynamic text such as displaying current state.
    '''

    def __init__(self, widgets: List[Widget], text: str=None, getText: Callable=None):
        '''ARGUMENTS
        widgets: the parent widget(s) of the ToolTip. The tooltip will show when the widget(s) is hovered.
        
        One of the following must be included:
        text: static text to be displayed in the tooltip
        getText: function to execute to return the text of the tooltip.

        RAISES
        ValueError: Either text or getText must be given.
            One of the two arguments is required.

        ValueError: One or more widgets' masters are unequal.
            Every widget must have the same master.
        '''

        if text is None and getText is None:
            raise ValueError("Either text or getText must be given")

        self._widgets=widgets
        self._master=self._widgets[0].master

        #verifying that all masters are the same
        for widget in self._widgets:
            if widget.master is not self._master:
                raise ValueError("One or more widgets' masters are unequal")

        #self becomes an instance of Toplevel
        Toplevel.__init__(self, master=self._master)
        
        #hide the toplevel immediately and remove its border + exit buttons
        self.withdraw()
        self.overrideredirect(True)

        # handle the text
        if text is not None:
            self.label=Label(master=self, text=text)
            self.label.pack()
            self.getText=None

        else:
            self.label=Label(master=self, text="")
            self.label.pack()
            self.getText=getText

        # bind the event handlers
        for widget in self._widgets:
            widget.bind("<Enter>", self.display)  # on mouse over
            widget.bind("<Motion>", self.goToWidget)  # when the mouse moves on _widgets
            widget.bind("<Leave>", self.die)  # on mouse off
        

    def display(self, event=None):  #the context is taken in to silence it
        '''Wrapper for Toplevel.deiconify to show the popup when needed.
        Necessary because events pass a context object into the callback so
        deiconify gets unexpected arguments'''

        if self.getText is not None:
            self.label.config(text=self.getText())

        self.deiconify()  # display self


    def die(self, event=None):  #again the context must be silenced
        '''Wrapper for Toplevel.withdraw to make the popup disappear.
        Necessary due to the event object passed to an event's callback'''

        self.withdraw()  # make self invisible


    def goToWidget(self, event):
        '''Moves the tip to where the cursor is instead of the top left corner'''

        # move to up and to the right of the cursor
        self.geometry(f"+{event.x_root+10}+{event.y_root+10}")  # not exactly placed on cursor to avoid interferance
        self.display()


class ToggleButton:
    '''
    Button that toggles its state when clicked.
    Uses a ToolTip to state its state.
    
    ATTRIBUTES
    button: tkinter.Button
        The wrapped button
    factory: WidgetFactory
        The factory that is used to build the Button.
    commands: List[Callable]
        The commands to be called on click.
    colours: Tuple[str, str]
        The fg colours to be used depending on state.
        Format: colours[0]: off state, colours[1]: on state.
    popouts: List[Widget]
        The widgets that will appear on the on state.
    showErrors: bool
        Whether to show errors when executing the commands.
    __state: bool property
        The on/off state of the button. DO NOT MODIFY.
    get: bool property
        Wrapped for self.state for compatibility with Pages.FormPage.
    '''

    #attributes
    __state=False

    def __init__(self, factory, coords: Tuple[int, int], command: Callable=None,
       fgColours: Tuple[str, str] = ("red", "green"), popouts: Tuple[Widget,] = (),
        showErrors: bool = True, **kwargs):
        '''Wraps the widget factory to create a button that can toggle its state
        
        ARGUMENTS
        factory: an instance of Modules.MyUtils.WidgetFactory.
        Used to build the widgets.
        coords: tuple of float coordinates to place the button at
        command: the function to be called upon state toggle as well as toggling the state.
        Must be anonymous.
        fgColours: tuple of strings of the colours to toggle between.
        Format= ({state=off colour}, {state=on colour})
        Defaults to (red, green)
        popouts: placed widgets to popout upon state change.
        showErrors: Whether to show errors when executing the commands.
        **kwargs: dict of extra settings for the button. Do not include the command
        '''

        def validatePopoutType(var):
            '''Checks if var is a tkinter variable type'''
            #type enforcing is not a good practice
            #this should be patched if it becomes a problem
            validTypes=[StringVar, IntVar, DoubleVar, BooleanVar]
            
            #checks against every type
            for type in validTypes:
                if isinstance(var, type):
                    return True

            #if list of type is exhausted, it must be of the wrong type
            raise TypeError("Popout var is not a tkinter type")


        self.factory=factory
        self.showErrors = showErrors

        #set commands
        self.commands=[self.stateChange] #list of anonymous functions to call upon button press

        if command is not None:
            self.commands.append(command)

        #create button
        self.button=factory.generalBuilder(Button, (coords[0], coords[1]),\
            relief="raised", **kwargs)

        #set colours
        self.colours = fgColours
        self.button.config(fg=self.colours[0])

        #handling popouts
        # This area is messy. It should be revised
        self.popouts = []
        for popout in popouts:
            info = popout.place_info()
            # get all info to reduce code density later
            relx, rely, x, y, anchor = float(info["relx"]), float(info["rely"]),\
                int(info["x"]), int(info["y"]), info["anchor"]

            #check if relative. If relative is deliberately 0, it doesn't matter if changed to absolute
            if (any((relx, rely)) > 0) and (x == 0 and y == 0):
                self.popouts.append((popout, (info["relx"], info["rely"]), True, anchor))

            else:
                self.popouts.append( (popout, (info["x"], info["y"]) , False, anchor))

            popout.place_forget()

        self.commands.append(self.popOutTextBox)

        #allowing tooltips to appear to show state
        #for accessibility I don't want to rely on colours only to show state
        self._tooltip=ToolTip([self.button], getText=lambda: f"State: {self.state}")

        self.button.config(command= self.callCommands)


    def callCommands(self):
        '''Wrapper to call each command.'''

        for command in self.commands:
            try:
                command()

            except Exception:
                if self.showErrors:
                    print_exc()


    def stateChange(self):
        '''Toggles the state of the button'''

        #changing the state
        self.__state=not self.__state

        #choosing the colour to change the fg attribute to
        #0=off, 1=on
        if self.__state:
            index=1
            self.button.config(relief="sunken")

        else:
            index=0
            self.button.config(relief="raised")

        self.button.config(fg=self.colours[index])


    def popOutTextBox(self):
        if self.state:
            for popout, coords, relative, anchor in self.popouts:
                if relative:
                    popout.place(relx = coords[0], rely = coords[1], anchor = anchor)

                else:
                    popout.place(x = coords[0], y = coords[1], anchor = anchor)

        else:
            for widget, *_ in self.popouts:
                widget.place_forget()

    #getters
    @property
    def state(self):
        '''Getter for self.state'''
        return self.__state


    # for Pages.FormPage compatibility
    def get(self) -> bool:
        """Get the state."""
        return self.__state


class DimensionGetter(Button):
    '''Prints the dimensions of the master on click. Developer tool'''

    def __init__(self, master: Union[Tk, Widget]):
        '''Adds a button to master to track its dimensions
        '''

        self.master = master
        super().__init__(master, text = "Print Dimensions",
            command = lambda: print(f"{self.master.winfo_width()},{self.master.winfo_height()}"))
        self.pack()
        

class FormField:
    """
    Wraps information about a field in a form.
    
    ATTRIBUTES
    field: Widget
        The attached Widget.
    get: Any property
        The value returned by field.get()
    validation: Callable
        The validation check attached to the field.
        Should take one argument (.get's value will be passed here).
        ^ how to do above: lambda x: func(x, *args, **kwargs)
    validationPassed: bool
        Whether .validation failed upon calling .value
    name: str
        The name to describe what the field contains.
    """

    class Validate:
        """Decorator to call the validation check before getting the value"""

        def __init__(self, func: Callable, *args):
            self.func = func


        def __call__(self, instance: 'FormField'):
            def inner(*args, **kwargs):
                # call validation and the function
                instance.validationPassed = instance.validation(self.field.get())
                return self.func(instance, *args, **kwargs)

            return inner()


    def __init__(self, field: Widget, validationCheck: Callable = None, name: str = ""):
        """
        ARGUMENTS
        field:
            The widget to attach to the instance. Must have a `.get` method.
        validationCheck:
            The function to call when fetching the field value.
            For multiple checks: use customCheck use
            MyUtils.callbacks.Callback.
        name:
            The name to describe what the field contains.
        """

        # validate if field is compatible with a form
        if hasattr(field, "get"):
            self.field = field

        else:
            raise AttributeError("field has no attribute `get`.")
        
        # validation check
        if not validationCheck:
            validationCheck = lambda value: CHECKTYPES["defaultCheck"](value)

        self.validation = validationCheck

        # name
        self.name = name


    @property
    @Validate
    def get(self) -> Any:
        """Get the value of the field"""

        return self.field.get()

    # CHECKS
    def attachValidation(self, checkType: str, *args, customCheck: Callback = None, **kwargs):
        """Put a validation check on the target field.

        ARGUMENTS
        checkType:
            The type of validation out of these options:
            lengthCheck, withinCheck, withoutCheck, 
            typeCheck, isUniqueCheck, customCheck.
            Look at the .__doc__s of their respective methods for more details.
        customCheck:
            Pass this if checkType = customCheck.
        """

        # assign the callback as a method of target
        if not customCheck:
            try:
                func = CHECKTYPES[checkType]
                self.validation = lambda value: func(value, *args, **kwargs)

            except KeyError:  # provide better error if invalid checkType
                raise ValueError("Invalid checkType")

        else:
            assert (customCheck is not None and callable(customCheck))  # ensure a callable was passed in
            self.validation = customCheck