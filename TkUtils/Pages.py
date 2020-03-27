'''This module contains all of the page templates.'''
from tkinter import *
from .factory import WidgetFactory
from .Widgets import Popup, FormField
from typing import *
from pickle import load, dump, UnpicklingError

# inherit from Toplevel to prevent a runtime error if this isn't set as the root window
class WindowPage(Toplevel):
    """
    Create default page for widgets to be placed on. Supports multiple pages.
    This is not well-optimised for performance however it runs plenty fast.
    This can be rewritten for better performance.
    
    ATTRIBUTES
    factories: MyUtils.WidgetFactory dict. name : WidgetFactory
        Used for building widgets.
    settingsFile: str
        File path for the settings PKL file.
    data: dict
        Any data to share between all children.
    _children:  list
        WindowPage subclass instances bound to this instance as their main window..
    _background: tkinter.Frame
        That serves as the parent for all widgets.
    _movementButtons: tkinter.Button list
        Button that move to the children.
    _moveButtonSpacing: float tuple
        The relative x, y to increment per child when placing the movement buttons.
    _themeIndex: str
        The key for the current theme.
    backgroundSettings: dict
        Kwargs for _background. Used to set image backgrounds etc.
    """

    # ATTRIBUTES
    _movementButtons: List[Button] = []

    def __init__(self, factories: List[WidgetFactory] = None, children: List['WindowChild'] = [],
        settingsFile: str = None, backgroundSettings: dict = {}, TkSettings: dict = {},
         moveButtonSpacing: Tuple[float, float] = (0.2, 0.1), data: dict = {}):
        """
        Create background window, 
        ARGUMENTS
        factories:
            The themes to be used. defaultAttrs[master] will be changed to self.background.
            The first element is the default theme
            If None: a default WidgetFactory instance will be created. 
        children: 
            Any already-instantiated WindowChilds to bind to this instance
        settingsFile:
            The PKL file where the settings are/will be stored. Any unfilled headers will be filled with defaults.
            If None: create file in current directory and dump default settings there.
        backgroundSettings:
            Any settings for self._background.
        TkSettings: 
            Any settings for the tkinter.Tk instance.
        data:
            Any data to share between all children.
        """

        # instantiate tkinter.Tk
        super().__init__(**TkSettings)

        # factories
        if not factories:
            factories = {"default" : WidgetFactory()}

        self.factories = {factory.name : factory for factory in factories}

        # data
        self.data = data

        # settingsFile
        self._validateSettings(settingsFile)

        # set up current theme as currently selected theme in settings, if exists
        with open(self.settingsFile, "rb") as f:
            settings = load(f)
            self._themeKey = settings["theme"]["name"]

        # children
        self._children = children

        # _background
        self.backgroundSettings = backgroundSettings
        self.createBackground()
        
        # update master for self.factories
        for factory in self.factories.values():
            factory.defaultAttrs["master"] = self._background

        # create movement buttons
        self._moveButtonSpacing = moveButtonSpacing
        self.placeMovePageButtons()

    
    # THEME METHODS
    def updateSettings(self, toInsert: dict):
        '''Add toInsert to self.settingsFile, overwriting if key exists'''

        #update settings
        with open(self.settingsFile, "rb+") as f:
            settings = load(f)

            # merge dicts
            settings.update(toInsert)

            # go back to the start and overwrite
            f.seek(0)
            dump(settings, f)


    def resetSettings(self):
        """Set the settings file to defaults."""
        with open(self.settingsFile, "wb") as f:
            dump({"theme" : WidgetFactory().writable()})


    def changeTheme(self, key: str, silencePopup: bool = False):
        '''Change to the target factory (theme).
        
        ARGUMENTS
        key: 
            The key of the target theme
        silencePopup:
            Don't show a Popup. For internal theme switching.'''

        #update index
        self._themeKey = key

        # update settings
        self.updateSettings({"theme" : self.currentTheme.makeWritable()})

        if not silencePopup:
            Popup("Switch pages to apply the theme.", title = "Theme Switched!")


    def placeThemeChoice(self, relCoords: Tuple[float, float]):
        """A default implementation of a change theme menu.
        Places a tkinter.OptionMenu to select between each theme
        
        relCoords:
            The relative co-ordinates to place it at."""

        # create traced var - the var will act as its own submit button
        targetTheme = StringVar(value = self._themeKey)
        targetTheme.trace("w", lambda *args : self.changeTheme(targetTheme.get()))  # ignore the context args

        # create options
        options = [factory.name for factory in self.factories.values()]
        
        menu = self.currentTheme.optionBuilder(targetTheme, options)

        menu.place(relx = relCoords[0], rely = relCoords[1])


    @property
    def currentTheme(self) -> WidgetFactory:
        return self.factories[self._themeKey]


    def _validateSettings(self, settingsFile: str):
        """Create the settings file if it doesn't exist and ensure all headers are filled."""

        # create file if not exists
        if not settingsFile:
            import os.path as path  # don't flood the namespace
            
            self.settingsFile = path.join(path.dirname(path.realpath(__file__)), "settings.pkl")

        else:
            self.settingsFile = settingsFile
                
        # ensure all headers are filled
        defaults = {
            "theme" : self.factories[list(self.factories.keys())[0]].makeWritable(),  # save a random theme
        }

        with open(self.settingsFile, "rb+") as f:
            # ensure it's not empty
            try:
                load(f)

            except (UnpicklingError, EOFError):  
                dump({"temp" : "temp"}, f)

            # check if each header exists
            f.seek(0)
            defaultHeaders = list(defaults.keys())
            fileKeys = load(f).keys()
            toWrite = {pair[0] : pair[1] for i, pair in enumerate(defaults.items()) if defaultHeaders[i] not in fileKeys}

        # overwrite file
        self.updateSettings(toWrite)


    # DRAWING METHODS
    def movePage(self, target: 'WindowChild', *args, **kwargs):
        '''Clear page and draw target page with *args and **kwargs'''

        try:
            self.clearPage()
            self.placeMovePageButtons()

        except:
            Popup("Failed to switch pages", "Move Page Error!")

        target(*args, **kwargs)


    def placeMovePageButtons(self):
        '''Create buttons to move to each child'''

        x = 0
        y = 0

        for child in self._children:
            # check for screen overflow
            if x >= 1:
                y += self._moveButtonSpacing[1]
                x = 0

            # place button
            button = self.currentTheme.generalBuilder(Button, (x, y), relative = True, text = child.name)

            x += self._moveButtonSpacing[0]

            self._movementButtons.append(button)


    def clearPage(self):
        '''Delete all widgets and redraw movement buttons'''

        self._background.destroy()
        self.createBackground()
        self.placeMovePageButtons()


    @staticmethod
    def clearWidgets(widgets: List[Widget]):
        '''Remove all target widgets from the screen but does not delete them.

        widgets: the target widgets to remove'''
        
        for widget in widgets:
            widget.place_forget() 


    def createBackground(self):
        '''Create background tkinter.Frame'''

        self._background = self.currentTheme.generalBuilder(Frame, (0.5, 0.5), anchor = "center",
            relative = True, master = self, fg = None, ignore = ["fg"], relheight = 1, relwidth = 1,
            **self.backgroundSettings)
    

    # CHILDREN HANDLING
    def addChild(self, child: 'WindowChild'):
        """Add child to self._children and redraw the movement buttons"""

        # prevent random types from being added to _children
        if not isinstance(WindowChild):
            raise TypeError(f"Unsupported operand type(s) for +: '{type(target)}' and 'WindowPage'")

        self._children.append(child)

        self.clearWidgets(self._movementButtons)
        self.placeMovePageButtons()


    def removeChild(self, target: 'WindowChild'):
        """
        Remove the WindowChild at _children[index]
        and redraw the movement buttons
        """

        # delete the child
        del self._children[self._children.index(target)]

        # create the movement buttons again
        self.clearWidgets(self._movementButtons)
        self.placeMovementButtons()


    # DUNDER METHODS
    # support `for child in WindowPage`
    def __getitem__(self, index: int) -> 'WindowChild':
        """Allow iteration over self._children"""

        return self._children[index]


    # support `len(WindowPage)`
    def __len__(self) -> int:
        """Get the number of fields."""

        return len(self._children)


    # support `WindowChild in WindowPage`
    def __contains__(self, value: 'WindowChild') -> bool:
        """Check if value is in self.fields"""

        return value in self._children


    # support `WindowPage + WindowChild`
    def __add__(self, target: 'WindowChild'):
        """Register a new WindowChild."""

        self.addChild(target)


    # support `WindowPage - WindowChild`
    def __sub__(self, target: 'WindowChild'):
        """Unregister the target from _children."""

        self.removeChild(target)


    # output a pretty view when `print` is called
    def __str__(self) -> str:
        """Output a pretty view of this object's attributes."""

        return f"""WindowPage with children: {self._children},
themes: {self.factories},
settingsFile: {self.settingsFile},
data: {self.data},
background: {self._background},
movementButtons: {self._movementButtons},
moveButtonSpacing: {self.moveButtonSpacing},
themeIndex: {self._themeIndex},
backgroundSettings: {self.backgroundSettings}
"""


class WindowChild(WindowPage):
    """Base class for all WindowPage children
    
    ATTRIBUTES
    _parent : WindowPage that this is assigned to
    name: what will appear on its movement button
    """

    # ATTRIBUTES

    def __init__(self, parent: WindowPage, name: str):
        """Registers the instance to its parent
        
        ARGUMENTS
        parent: the WindowPage this instance is bound to
        name: the name that will be displayed on its movement button
        """
        
        self._parent = parent
        self.name = name

        self._parent.addChild(self)


    @property
    def parent(self) -> WindowPage:
        """Get the parent of this page."""

        return self._parent


class FormPage(WindowChild):
    """
    Provides useful utils for form screens.

    ATTRIBUTES
    fields: list of FormField
        All of the Widgets attached to the form.
    submissionResults: dict with keys:
        results: 
            list of tuples: 
                (name of field, value of field)
        failed:
            list of failed Widgets
    """

    # ATTRIBUTES
    # neccessary due to the callback nature of the submit method
    submissionResults = {"results" : [], "failed" : []}


    def __init__(self, parent: WindowPage, fields: List[FormField], name: str = ""):
        """
        ARGUMENTS
        parent:
            The window to attach to.
        fields:
            The FormFields attached to the form. Must have a `get` method.
        name:
            The name of this form.
        """

        # start up WindowChild instance
        super().__init__(parent, name)

        # ensure all fields have a `get`
        for field in fields:
            try:
                hasattr(field, "get")

            except AttributeError:
                raise ValueError("All fields must have a `get` method.")

        self.fields = fields


    # dunder methods
    def __getitem__(self, index: int) -> FormField:
        """Get the next field. Allows for-each iteration."""

        return self.fields[index]


    def __len__(self) -> int:
        """Get the number of fields."""

        return len(self.fields)


    def __contains__(self, value: FormField) -> bool:
        """Check if value is in self.fields"""

        return value in self.fields


    # SUBMISSION
    def basicSubmit(self):
        """Get the value of each field. No validation checks are applied.
        
        RETURNS
        values sent to self.submissionResults as dict with keys:
            results : 
                list of tuples:
                    (name of field, value of field)
            failed: empty list"""

        self.submissionResults = {"results" : [(field.name, field.value) for field in self.fields],
            "failed" : []}


    def submit(self):
        """
        Get the values of each field, after their validation checks

        RETURNS
        sends this to self.submissionResults:
        dict with keys:
            results: 
                list of tuples: 
                    (name of field, value of field)
            failed:
                list of failed Widgets
        """

        output = {"results" : [], "failed" : []}

        # build results dict
        for field in self:
            result = field.get
            if field.validationPassed:
                output["results"].append((field.name, result))

            else:
                output["failed"].append(field)

        self.submissionResults = output


    def placeSubmitButton(self, coords: Tuple[float, float], basic: bool = True):
        """
        Place a default submit button.

        ARGUMENTS
        basic:
            Whether .basicSubmit() will be used.
        """

        submitButton = self._parent.currentTheme.generalBuilder(Button, coords,
            text = "Submit", relative = True)

        if basic:
            submitButton["command"] = self.basicSubmit

        else:
            submitButton["command"] = self.submit


    def massAddValidation(self, fields: Iterable[FormField,], check: Callable = None,
        checks: Iterable[Callable] = None):
        """Add either one check or many different checks to widgets.

        ARGUMENTS
        widgets:
            The target widgets to add validation checks to.
        check:
            The check to add to every widget.
        checks:
            The checks to add. Should be parallel to fields.

        RAISES
        AssertionError: either check or checks must be passed."""

        # ensure either check or checks is passed
        assert (check or checks)

        if check:
            [field.attachValidation("customCheck", customCheck = check) for field in fields]

        else:
            [field.attachValidation("customCheck", customCheck = checks[i])
                for field in enumerate(fields)]