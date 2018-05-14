'''
A collection of useful functions to use in MSAA clients.

Inspired by pyatspi:
http://live.gnome.org/GAP/PythonATSPI

@author: Eitan Isaacson
@copyright: Copyright (c) 2008, Eitan Isaacson
@license: LGPL

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Library General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Library General Public License for more details.

You should have received a copy of the GNU Library General Public
License along with this library; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
'''

import faulthandler
import signal
import sys
import threading
import traceback

import constants

import collections

import ctypes
from ctypes import windll, oledll, POINTER, byref, c_int
from comtypes.automation import VARIANT
from comtypes import CoInitializeEx
from comtypes import CoUninitialize
from comtypes import COINIT_MULTITHREADED
from comtypes.gen.Accessibility import IAccessible
from comtypes import COMError, IServiceProvider
from comtypes.client import GetModule, CreateObject
import comtypesClient
from constants import CHILDID_SELF, \
    UNLOCALIZED_ROLE_NAMES, \
    UNLOCALIZED_STATE_NAMES, \
    UNLOCALIZED_IA2_STATE_NAMES, \
    UNLOCALIZED_IA2_ROLE_NAMES, \
    UNLOCALIZED_IA2_RELATION_TYPES, \
    UNLOCALIZED_EVENT_NAMES, \
    IA2_TEXT_OFFSET_LENGTH

# IA2Lib = ctypes.WinDLL('C:\Program Files (x86)\NVDA\lib64\IAccessible2Proxy.dll')
IA2Lib = comtypesClient.GetModule('ia2.tlb')
IALib  = comtypesClient.GetModule('oleacc.dll').IAccessible

class AccessibleElement:

  test_id               = ''
  role                  = ''
  ia2_role              = ''
  localizedExtendedRole = ''
  accName               = ''
  accValue              = ''
  ia2_value             = ''
  accDescription        = ''
  states                = []
  objectAttributes      = []
  textAttributes        = []
  relations             = []
  interfaces            = []
  accKeyboardShortcut   = ''
  groupPosition         = ''
  columnExtent          = ''
  rowExtent             = ''

  ia2_value             = ['0','0','0']
  ia2_value_min         = '0'
  ia2_value_current     = '0'
  ia2_value_max         = '0'


  def __init__(self, ao):
    self.test_id               = get_id(ao)
    if len(self.test_id) == 0:
        return
    self.role                  = get_role(ao)
    if len(self.role) == 0:
        return
    self.ia2_role              = get_ia2_role(ao)
    self.localizedExtendedRole = get_extended_role(ao)
    self.accName               = get_name(ao)
    self.accValue              = get_value(ao)
    self.ia2_value             = get_ia2_value(ao)
    self.accDescription        = get_description(ao)
    self.states                = get_state_set(ao)
    self.objectAttributes      = get_ia2_attribute_set(ao)
    self.textAttributes        = get_ia2_text_attribute_set(ao)
    self.relations             = get_ia2_relation_set(ao)
    self.interfaces            = get_interface_set(ao)
    self.accKeyboardShortcut   = get_keyboard_shortcut(ao)
    self.groupPosition         = get_ia2_group_position(ao)
    self.columnExtent          = get_column_extent(ao)
    self.rowExtent             = get_row_extent(ao)

    if self.ia2_value:
      self.ia2_value_min     = str(self.ia2_value[0])
      self.ia2_value_current = str(self.ia2_value[1])
      self.ia2_value_max     = str(self.ia2_value[2])

      # This is fix to be compatible with ARIA 1.1 Test cases and WPT
      if self.ia2_value_min.find(".0") >= 0:
        self.ia2_value_min = self.ia2_value_min[:-2]

      if self.ia2_value_current.find(".0") >= 0:
        self.ia2_value_current = self.ia2_value_current[:-2]

      if self.ia2_value_max.find(".0") >= 0:
        self.ia2_value_max = self.ia2_value_max[:-2]


  def __str__(self):

    s = ''

    if self.test_id:
        s += "            ID: " + self.test_id + "\n"
    else:
        pass

    s += "           ROLE: " + self.role + "\n"

    if self.localizedExtendedRole:
        s += "  EXTENDED ROLE: " + str(self.localizedExtendedRole) + "\n"

    if self.accName:
        s += "           NAME: " + self.accName + "\n"

    if self.accValue:
        s += "          VALUE: " + self.accValue + "\n"

    if self.ia2_value:
        s += "      IA2 VALUE_MIN: " + self.ia2_value_min     + "\n"
        s += "  IA2 VALUE_CURRENT: " + self.ia2_value_current + "\n"
        s += "      IA2 VALUE_MAX: " + self.ia2_value_max     + "\n"


    if self.accKeyboardShortcut:
        s += "    KB SHORTCUT: " + self.accKeyboardShortcut + "\n"


    if self.accDescription:
        s += "    DESCRIPTION: " + self.accDescription + "\n"

    s += "        STATES: " + str(self.states) + "\n"

    s += "     ATTRIBUTES: " + str(self.objectAttributes) + "\n"
    s += "TEXT ATTRIBUTES: " + str(self.textAttributes) + "\n"
    s += "      RELATIONS: " + str(self.relations) + "\n"
    s += "     INTERFACES: " + str(self.interfaces) + "\n"

    if self.groupPosition:
        s += " GROUP POSITION: " + str(self.groupPosition) + "\n"

    if self.rowExtent:
        s += "     ROW EXTENT: " + self.rowExtent + "\n"

    if self.columnExtent:
        s += "  COLUMN EXTENT: " + self.columnExtent + "\n"

    return s


class AccessibleDocument:

  def __init__(self, ao):
    self.ao = ao
    self.busy = False
    self.events = []
    self.test_elements = []
    self.document = AccessibleElement(ao)
    self.uri = get_value(ao)
    self.updateTestElements()

  def __str__(self):

    s = ""
    s += "\n===== Accessible Document Object =====" + "\n"
    s += str(self.document)
    s += "\nEVENT TYPES: " + str(self.events) + "\n"

    for elem in self.test_elements:
      s += "\n--- Accessible Element Objects ---" + "\n"
      s += str(elem)

    return s

  def addEvent(self, event_type):

    event_name = UNLOCALIZED_EVENT_NAMES[event_type]

    if not event_name in self.events:
        self.events.append(event_name)
        return True

    return False

  def updateTestElements(self):
    self.test_elements = []

    pred = lambda x: has_id(x)
    test_elems = findAllDescendants(self.ao, pred)

    for test_elem in test_elems:
      id = get_id(test_elem)
      if id != 'manualMode' and id != 'log' and id != 'ATTAmessages':
        self.test_elements.append(AccessibleElement(test_elem))



def cleanString(s):
  try:
    return s.encode('ascii', 'ignore').decode("utf-8")
  except:
    return s

def getDesktop():
  desktop_hwnd = windll.user32.GetDesktopWindow()
  desktop_window = accessibleObjectFromWindow(desktop_hwnd)
  for child in desktop_window:
    if child.accRole() == constants.ROLE_SYSTEM_CLIENT:
      return child
  return None

def getForegroundWindow():
  return accessibleObjectFromWindow(
    windll.user32.GetForegroundWindow())

def accessibleObjectFromWindow(hwnd):
  ptr = POINTER(IAccessible)()
  res = oledll.oleacc.AccessibleObjectFromWindow(
    hwnd,0,
    byref(IAccessible._iid_),byref(ptr))
  return ptr

def accessibleObjectFromEvent(event):
  if not windll.user32.IsWindow(event.hwnd):
    return None
  ptr = POINTER(IAccessible)()
  varChild = VARIANT()
  res = windll.oleacc.AccessibleObjectFromEvent(
    event.hwnd, event.object_id, event.child_id,
    byref(ptr), byref(varChild))
  if res == 0:
    child=varChild.value
    return ptr.QueryInterface(IAccessible)
  else:
    return None

def accessible2FromAccessible(pacc, child_id):
    debug = ""

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessible2):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            debug += "Got IServiceProvider"
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessible2)
            debug += "Got IA2Lib.IAccessible2"
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
            print "[accessible2FromAccessible] EXCEPTION cannot get IA2 object:", str(e)

    return None

def accessibleDocumentFromAccessible(pacc, child_id):

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessibleDocument):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessibleDocument)
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
          return None

def accessibleImageFromAccessible(pacc, child_id):

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessibleImage):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessibleImage)
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
          return None

def accessibleTextFromAccessible(pacc, child_id):

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessibleText):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessibleText)
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
          return None

def accessibleHypertext2FromAccessible(pacc, child_id):

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessibleHypertext2):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessibleHypertext2)
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
          return None

def accessibleTable2FromAccessible(pacc, child_id):

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessibleTable2):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessibleTable2)
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
          return None

def accessibleTableCellFromAccessible(pacc, child_id):

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessibleTableCell):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessibleTableCell)
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
          return None

def accessibleValueFromAccessible(pacc, child_id):

    if not isinstance(pacc, IAccessible):
        try:
            pacc = pacc.QueryInterface(IAccessible)
        except COMError:
            raise RuntimeError("%s Not an IAccessible"%pacc)

    if child_id==0 and not isinstance(pacc,IA2Lib.IAccessibleValue):
        try:
            s=pacc.QueryInterface(IServiceProvider)
            pacc2=s.QueryService(IALib._iid_, IA2Lib.IAccessibleValue)
            if not pacc2:
                raise ValueError
            else:
                return pacc2

        except Exception as e:
          return None

def com_coinitialize():
    CoInitializeEx(COINIT_MULTITHREADED)
    return

def com_couninitialize():
    CoUninitialize()
    return

def get_value(pacc):
    return pacc.accValue(CHILDID_SELF)


def get_child_count(pacc):
    return pacc.accChildcount

def get_child_at_index(pacc, index):
    try:
      child = pacc.accChild(index)
    except:
      child = None
    return child

def get_children(pacc):
    """Returns the children of obj or [] upon failure or absence of children."""

    children = []

    try:
        count = pacc.accChildCount
    except:
        print('[utils][get_children][count][exception]')
        return []

    try:
        for i in range(count):
#          print('[utils][get_children][i]: ' + str(i))
          child = pacc.accChild(i)
#          print('[utils][get_children][child]: ' + str(child))
          children.append(child)
    except:
#        print('[utils][get_children][children][exception]')
        return []


    return children

def get_description(pacc):
    return cleanString(pacc.accDescription(CHILDID_SELF))

def get_name(pacc):
    return pacc.accName(CHILDID_SELF)

def get_keyboard_shortcut(pacc):

    value = ''

    try:
        value =  pacc.accKeyboardShortcut(CHILDID_SELF)
    except Exception as e:
        print "ERROR cannot get keyboard shortcut:", str(e)

    return value


def get_role(pacc):

    value = ''

    try:
        value = str(pacc.accRoleName())
    except Exception as e:
        print "ERROR cannot get IA2 extended role:", str(e)

    return value

def get_extended_role(pacc):

    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    try:
        value = pacc2.localizedExtendedRole

        if value == '':
            value = 'null'

    except Exception as e:
        print "ERROR cannot get IA2 extended role:", str(e)
        return ''

    return value

def get_ia2_role(pacc):
    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessible2):
      if pacc2.role() == 0:
          return UNLOCALIZED_IA2_ROLE_NAMES[0]
      else:
        if pacc2.role() < 62:
          return UNLOCALIZED_ROLE_NAMES[pacc2.role()]
        else:
          return UNLOCALIZED_IA2_ROLE_NAMES[pacc2.role()]

    return ""

def get_ia2_relation_set(pacc):
    list = []

    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    try:
        for i in range (pacc2.nRelations):
          type = pacc2.relation(i).relationType
          list.append(UNLOCALIZED_IA2_RELATION_TYPES[type])
#          list.append(type)

    except Exception as e:
        print "ERROR cannot get IA2 relation:", str(e)
    return list

def get_ia2_group_position(pacc):
    value = (-1, -1, -1)

    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    try:
        value = pacc2.groupPosition

    except Exception as e:
        print "ERROR cannot get IA2 group postion:", str(e)

    values = []
    values.append('groupLevel:' + str(value[0]))
    values.append('similarItemsInGroup:' + str(value[1]))
    values.append('positionInGroup:' + str(value[2]))

    return values


def get_state_set(pacc):
    list = []

    states = pacc.accState(CHILDID_SELF)
    for item in UNLOCALIZED_STATE_NAMES:
      if item & states:
        list.append(UNLOCALIZED_STATE_NAMES[item])

    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)

    if isinstance(pacc2, IA2Lib.IAccessible2):
      states = pacc2.states
      for item in UNLOCALIZED_IA2_STATE_NAMES:
        if item & states:
          list.append(UNLOCALIZED_IA2_STATE_NAMES[item])

    return list

def get_ia2_state_set(pacc):
    list = []

    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)

    if isinstance(pacc2, IA2Lib.IAccessible2):
      states = pacc2.states
      for item in UNLOCALIZED_IA2_STATE_NAMES:
        if item & states:
          list.append(UNLOCALIZED_IA2_STATE_NAMES[item])

    return list

def get_ia2_attributes(pacc):
    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessible2):
      return pacc2.attributes

    return ""

def get_ia2_attribute_set(pacc):
    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessible2):
      attrs = pacc2.attributes.strip()
      if len(attrs) and attrs[-1] == ';':
        attrs = attrs[:-1]
      return attrs.split(';')

    return []

def get_ia2_text_attribute_set(pacc):
    pacc2 = accessibleTextFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleText):
        # -1 means using the constant
        try:
            [startOffset, endOffset, attrs] = pacc2.attributes(IA2_TEXT_OFFSET_LENGTH)
            if attrs and len(attrs) and attrs[-1] == ';':
                attrs = attrs[:-1]
                return attrs.split(';')
        except:
            pass

    return []

def get_type_set(pacc):
    list = []
    return list

def get_id(pacc):
    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessible2):
      attrs = pacc2.attributes.split(';')
      for attr in attrs:
        parts = attr.split(':')
        if len(parts) == 2 and parts[0] == 'id':
          return parts[1]

    return ""

def has_id(pacc):
    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessible2):
      attrs = pacc2.attributes.split(';')
      for attr in attrs:
        parts = attr.split(':')
        if len(parts) == 2 and parts[0] == 'id':
          return True

    return False



def get_interface_set(pacc):
    list = []

    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessible2):
      list.append('IAccessible2')

    pacc2 = accessibleDocumentFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleDocument):
      list.append('IAccessibleDocument')

    pacc2 = accessibleTextFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleText):
      list.append('IAccessibleText')

    pacc2 = accessibleHypertext2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleHypertext2):
      list.append('IAccessibleHypertext2')

    pacc2 = accessibleImageFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleImage):
      list.append('IAccessibleImage')

    pacc2 = accessibleTable2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleTable2):
      list.append('IAccessibleTable2')

    pacc2 = accessibleTableCellFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleTableCell):
      list.append('IAccessibleTableCell')

    pacc2 = accessibleValueFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleValue):
      list.append('IAccessibleValue')



    return list

def get_ia2_property_value(pacc, property):

    pacc2 = accessible2FromAccessible(pacc, CHILDID_SELF)

    if isinstance(pacc2, IA2Lib.IAccessible2):
      states = pacc2.states

      try:
        return states & constants[property]
      except:
        return -1

    return -1

def get_parent(pacc):
    return pacc.acc_parent

def get_ia2_value(pacc):

    pacc2 = accessibleValueFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleValue):
        list = []
        try:
            list.append(pacc2.minimumValue)
            list.append(pacc2.currentValue)
            list.append(pacc2.maximumValue)
            return list

        except Exception as e:
            print "[get_ia2_value] Exception cannot get IA2 value:", str(e)

        return None
    else:
        return None

def get_ia2_table_cell(pacc):

    pacc2 = accessibleTableCellFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleTableCell):
        try:
            return pacc2

        except Exception as e:
            print "[get_ia2_table_cell] Exception cannot get IA2 IAccessibleTableCell:", str(e)

        return None
    else:
        return None


def get_column_extent(pacc):

    pacc2 = accessibleTableCellFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleTableCell):
        try:
            return str(pacc2.columnExtent)

        except Exception as e:
            print "[get_column_extent] Exception cannot get IAccessibleTableCell::columnExtent", str(e)

        return None
    else:
        return None

def get_row_extent(pacc):

    pacc2 = accessibleTableCellFromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessibleTableCell):
        try:
            return str(pacc2.rowExtent)

        except Exception as e:
            print "[get_column_extent] Exception cannot get IAccessibleTableCell::rowExtent", str(e)

        return None
    else:
        return None




def get_relation_set(pacc):
    pacc2 = self.accessible2FromAccessible(pacc, CHILDID_SELF)
    if isinstance(pacc2, IA2Lib.IAccessible2):
        out = "Relation info:"
        try:
            out +=  "  Number(" + str(pacc2.nRelations) + ")\n\r "

        except Exception as e:
            print "ERROR cannot get IA2 nRelation:", str(e)

        try:
            for i in range (pacc2.nRelations):
              out +=  "[Type: " + pacc2.relation(i).relationType + "; "
              out +=  "Targets(" + str(pacc2.relation(i).nTargets) + ") "
              for j in range(pacc2.relation(i).nTargets):
                t = pacc2.relation(i).target(j)
                s=t.QueryInterface(IServiceProvider)
                oa2=s.QueryService(IALib._iid_, IA2Lib.IAccessible2)

                out += "'" + str(oa2) + "'"

              out += "]"

            return out

        except Exception as e:
            print "[get_relation_set] Exception cannot get IA2 relation:", str(e)

    return "None"


def findDescendant(acc, pred, breadth_first=False):
  '''
  Searches for a descendant node satisfying the given predicate starting at
  this node. The search is performed in depth-first order by default or
  in breadth first order if breadth_first is True. For example,

  my_win = findDescendant(lambda x: x.name == 'My Window')

  will search all descendants of x until one is located with the name 'My
  Window' or all nodes are exausted. Calls L{_findDescendantDepth} or
  L{_findDescendantBreadth} to start the recursive search.

  @param acc: Root accessible of the search
  @type acc: Accessibility.Accessible
  @param pred: Search predicate returning True if accessible matches the
  search criteria or False otherwise
  @type pred: callable
  @param breadth_first: Search breadth first (True) or depth first (False)?
  @type breadth_first: boolean
  @return: Accessible matching the criteria or None if not found
  @rtype: Accessibility.Accessible or None
  '''
  if breadth_first:
    return _findDescendantBreadth(acc, pred)

  for child in acc:
    try:
      ret = _findDescendantDepth(acc, pred)
    except Exception:
      ret = None
    if ret is not None: return ret

def _findDescendantBreadth(acc, pred):
  '''
  Internal function for locating one descendant. Called by L{findDescendant} to
  start the search.

  @param acc: Root accessible of the search
  @type acc: Accessibility.Accessible
  @param pred: Search predicate returning True if accessible matches the
  search criteria or False otherwise
  @type pred: callable
  @return: Matching node or None to keep searching
  @rtype: Accessibility.Accessible or None
  '''
  for child in acc:
    try:
      if pred(child): return child
    except Exception:
      pass
  for child in acc:
    try:
      ret = _findDescendantBreadth(child, pred)
    except Exception:
      ret = None
    if ret is not None: return ret

def _findDescendantDepth(acc, pred):
  '''
  Internal function for locating one descendant. Called by L{findDescendant} to
  start the search.

  @param acc: Root accessible of the search
  @type acc: Accessibility.Accessible
  @param pred: Search predicate returning True if accessible matches the
  search criteria or False otherwise
  @type pred: callable
  @return: Matching node or None to keep searching
  @rtype: Accessibility.Accessible or None
  '''
  try:
    if pred(acc): return acc
  except Exception:
    pass
  for child in acc:
    try:
      ret = _findDescendantDepth(child, pred)
    except Exception:
      ret = None
    if ret is not None: return ret

def findAllDescendants(acc, pred):
  '''
  Searches for all descendant nodes satisfying the given predicate starting at
  this node. Does an in-order traversal. For example,

  pred = lambda x: x.getRole() == pyatspi.ROLE_PUSH_BUTTON
  buttons = pyatspi.findAllDescendants(node, pred)

  will locate all push button descendants of node.

  @param acc: Root accessible of the search
  @type acc: Accessibility.Accessible
  @param pred: Search predicate returning True if accessible matches the
      search criteria or False otherwise
  @type pred: callable
  @return: All nodes matching the search criteria
  @rtype: list
  '''
  matches = []
  _findAllDescendants(acc, pred, matches)
  return matches

def _findAllDescendants(acc, pred, matches):
  '''
  Internal method for collecting all descendants. Reuses the same matches
  list so a new one does not need to be built on each recursive step.
  '''

  try:
      for child in acc:
        try:
          if pred(child): matches.append(child)
        except Exception:
          pass
        _findAllDescendants(child, pred, matches)
  except:
    pass

def findAncestor(acc, pred):
    if acc is None:
        # guard against bad start condition
        return None
    while 1:
        try:
            parent = acc.accParent.QueryInterface(IAccessible)
        except:
            parent = None
        if parent is None:
            # stop if there is no parent and we haven't returned yet
            return None
        try:
            if pred(parent): return parent
        except Exception:
            pass
        # move to the parent
        acc = parent

def printSubtree(acc, indent=0):
  print '%s%s' % (indent*' ', unicode(acc).encode('cp1252', 'ignore'))
  for child in acc:
    try:
      printSubtree(child, indent+1)
    except:
      pass

def windowFromAccessibleObject(acc):
  hwnd = c_int()
  try:
    res = windll.oleacc.WindowFromAccessibleObject(acc, byref(hwnd))
  except:
    res = 0
  if res == 0:
    return hwnd.value
  else:
    return 0

def getWindowThreadProcessID(hwnd):
  processID = c_int()
  threadID = windll.user32.GetWindowThreadProcessId(hwnd,byref(processID))
  return (processID.value, threadID)

def getAccessibleThreadProcessID(acc):
  hwnd = windowFromAccessibleObject(acc)
  return getWindowThreadProcessID(hwnd)
