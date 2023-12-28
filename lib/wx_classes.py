import sys
import wx

class FltRangeValidator(wx.Validator):
    """A float range validator for a TextCtrl"""
    def __init__(self, min_=-sys.maxsize, max_=sys.maxsize, negAllowed = False,
                 eLabel = "Invalid Value", required = True):
        """Initialize the validator
        @keyword min: min value to accept
        @keyword max: max value to accept

        """
        super(FltRangeValidator, self).__init__()
        #assert min_ >= 0, "Minimum Value must be >= 0"
        self._min = min_
        self._max = max_
        self._negAllowed = negAllowed
        self._label = eLabel
        self._required = required
        # Event managment
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        """Required override"""
        return FltRangeValidator(self._min, self._max, self._negAllowed, 
                                 self._label, self._required)

    def Validate(self, win):
        """Override called to validate the window's value.
        @return: bool
        """
        txtCtrl = self.GetWindow()
        val = txtCtrl.GetValue()
        isValid = False
        try:
            _test = float(val)
            isValid = True
        except ValueError:
            isValid = False
        if isValid:
            isValid = False
            digit = float(val)
            if digit >= self._min and digit <= self._max:
                isValid = True
        if len(val.strip()) < 1:
            #print "empty cell ", self._label, isValid
            if self._required:
                msg = "%s must be set" % (self._label)
                wx.MessageBox(msg,
                              self._label,
                              style=wx.OK|wx.ICON_ERROR)                  
            else:
                isValid = True
        elif not isValid:
            # Notify the user of the invalid value
            msg = "Input Value (%s) should fall between %d and %d" % \
                  (self._label, self._min, self._max)
            wx.MessageBox(msg,
                          self._label,
                          style=wx.OK|wx.ICON_ERROR)
        return isValid
    def OnChar(self, event):
        txtCtrl = self.GetWindow()
        key = event.GetKeyCode()
        isDigit = False
        try: 
            newVal = chr(key) 
        except ValueError:
            newVal = ''

        if self._negAllowed and newVal == '-':
            val = txtCtrl.GetValue()
            # value is empty - accept minus sign
            pos = txtCtrl.GetInsertionPoint()
            if pos == 0:
                if len(val):
                    if '-' not in val:
                        event.Skip()    
                else:
                    event.Skip()
                return
        elif newVal == '.':
            val = txtCtrl.GetValue()
            # value is empty - accept minus sign
            pos = txtCtrl.GetInsertionPoint()
            if len(val):
                if '.' not in val:
                    if len(val) == pos:
                        #print 'a'
                        event.Skip()   
                    elif val[pos] == '-':
                        #print 'b'
                        event.Veto()
                        return
            else:
                event.Skip()
        elif key < 256:
            
            isDigit = chr(key).isdigit()
            if key in (wx.WXK_RETURN,
                       wx.WXK_DELETE,
                       wx.WXK_BACK) or key > 255 or isDigit:
                if isDigit:
                    # Check if in range
                    val = txtCtrl.GetValue()
                    digit = chr(key)
                    pos = txtCtrl.GetInsertionPoint()
                    if pos == len(val):
                        val += digit
                    else:
                        val = val[:pos] + digit + val[pos:]
                    val = float(val)
                    
                event.Skip()
                return
        else:
            event.Skip()
            return

        if not wx.Validator.IsSilent():
            # Beep to warn about invalid input
            wx.Bell()

        return
    def TransferToWindow(self):
         """Overridden to skip data transfer"""
         return True
    def TransferFromWindow(self):
         """Overridden to skip data transfer"""
         return True 
     
class IntRangeValidator(wx.Validator):
    """An integer range validator for a TextCtrl"""
    def __init__(self, min_=0, max_=sys.maxsize, eLabel = "Invalid Value"):
        """Initialize the validator
        @keyword min: min value to accept
        @keyword max: max value to accept

        """
        super(IntRangeValidator, self).__init__()
        assert min_ >= 0, "Minimum Value must be >= 0"
        self._min = min_
        self._max = max_
        self._label = eLabel
        # Event managment
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        """Required override"""
        return IntRangeValidator(self._min, self._max, self._label)

    def Validate(self, win):
        """Override called to validate the window's value.
        @return: bool
        """
        txtCtrl = self.GetWindow()
        vals = txtCtrl.GetValue().split()
        popIndices = []
        for i, val in enumerate(vals):
            isValid = False
            if val.isdigit():
                digit = int(val)
                if digit >= self._min and digit <= self._max:
                    isValid = True
                
            if not isValid:
                popIndices.append(i)
            print(i, val, digit, isValid)
    
        if len(popIndices):
            # Notify the user of the invalid value
            msg = "Values must be between %d and %d" % \
                  (self._min, self._max)
            wx.MessageBox(msg,
                          self._label,
                          style=wx.OK|wx.ICON_ERROR)

        return isValid
    def OnChar(self, event):
        txtCtrl = self.GetWindow()
        key = event.GetKeyCode()
        isDigit = False
        if key < 256:
            isDigit = chr(key).isdigit()

        if key in (wx.WXK_RETURN,
                   wx.WXK_DELETE,
                   wx.WXK_BACK) or \
           key > 255 or isDigit:
            if isDigit:
                # Check if in range
                val = txtCtrl.GetValue()
                digit = chr(key)
                pos = txtCtrl.GetInsertionPoint()
                if pos == len(val):
                    val += digit
                else:
                    val = val[:pos] + digit + val[pos:]

                val = int(val)
                if val < self._min or val > self._max:
                    if not wx.Validator.IsSilent():
                        wx.Bell()
                    return
                
            event.Skip()
            return

        if not wx.Validator.IsSilent():
            # Beep to warn about invalid input
            wx.Bell()

        return
    def TransferToWindow(self):
         """Overridden to skip data transfer"""
         return True
    def TransferFromWindow(self):
         """Overridden to skip data transfer"""
         return True 
     
class IntsRangeValidator(wx.Validator):
    """An integer list range validator for a TextCtrl"""
    def __init__(self, min_=0, max_=sys.maxsize, eLabel = "Invalid Value"):
        """Initialize the validator
        @keyword min: min value to accept
        @keyword max: max value to accept

        """
        super(IntsRangeValidator, self).__init__()
        assert min_ >= 0, "Minimum Value must be >= 0"
        self._min = min_
        self._max = max_
        self._label = eLabel

        # Event managment
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        """Required override"""
        return IntsRangeValidator(self._min, self._max, self._label)

    def Validate(self, win):
        """Override called to validate the window's value.
        @return: bool
        """
        txtCtrl = self.GetWindow()
        vals = txtCtrl.GetValue().split()
        popIndices = []
        isValid = False
        for i, val in enumerate(vals):
            if val.isdigit():
                digit = int(val)
                if digit >= self._min and digit <= self._max:
                    isValid = True                
            if not isValid:
                popIndices.append(i)
        if len(vals) < 1:
            msg = "%s must be set" % (self._label)
            wx.MessageBox(msg,
                          self._label,
                          style=wx.OK|wx.ICON_ERROR)            
        if len(popIndices):
            # Notify the user of the invalid value
            msg = "%s is not valid" % (self._label)
            wx.MessageBox(msg,
                          self._label,
                          style=wx.OK|wx.ICON_ERROR)
        return isValid
    def OnChar(self, event):
        txtCtrl = self.GetWindow()
        key = event.GetKeyCode()
        isDigit = False
        try: 
            newVal = chr(key) 
        except ValueError:
            newVal = ''

        if newVal == ' ':
            event.Skip()
        elif key < 256:
            
            isDigit = chr(key).isdigit()
            if key in (wx.WXK_RETURN,
                       wx.WXK_DELETE,
                       wx.WXK_BACK) or key > 255 or isDigit:
                if isDigit:
                    # Check if in range
                    val = txtCtrl.GetValue()
                    digit = chr(key)
                    pos = txtCtrl.GetInsertionPoint()
                    if pos == len(val):
                        val += digit
                    else:
                        val = val[:pos] + digit + val[pos:]
                event.Skip()
                return
        else:
            event.Skip()
            return

        if not wx.Validator.IsSilent():
            # Beep to warn about invalid input
            wx.Bell()

        return
    def TransferToWindow(self):
         """Overridden to skip data transfer"""
         return True
    def TransferFromWindow(self):
         """Overridden to skip data transfer"""
         return True 
