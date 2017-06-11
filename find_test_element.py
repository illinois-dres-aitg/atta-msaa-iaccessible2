import pyia2
from pyia2.constants import CHILDID_SELF, \
    UNLOCALIZED_ROLE_NAMES, \
    UNLOCALIZED_STATE_NAMES
from pyia2.utils import IA2Lib

def accessible_object_information(ao):
    print("MSAA        ROLE: " + pyia2.get_role(ao))

    name = pyia2.get_name(ao)
    if name:
        print("MSAA        NAME: " + name)
    else:
        print("MSAA        NAME: none")

    value = pyia2.get_value(ao)
    if value:        
        print("MSAA       VALUE: " + value)
    else:
        print("MSAA       VALUE: none")
        
    desc = pyia2.get_description(ao)
    if desc:     
        print("MSAA DESCRIPTION: " + desc)
    else:
        print("MSAA DESCRIPTION: none")
        
    print("MSAA      STATES: " + str(pyia2.get_state_set(ao)))

    ao2 = pyia2.accessible2FromAccessible(ao, CHILDID_SELF)
    if isinstance(ao2, IA2Lib.IAccessible2):

        print("\nIA2       ROLE: " + pyia2.get_ia2_role(ao));
        print("IA2     STATES: " + str(pyia2.get_ia2_state_set(ao)))
        print("IA2 ATTRIBUTES: " + str(pyia2.get_ia2_attribute_set(ao)))
        print("IA2   RELATION: " + str(pyia2.get_ia2_relation(ao)))

    else:
        print "\nIA2 none"

    print("\nINTERFACES: " + str(pyia2.get_interface_set(ao)))


def event_cb(event):

    ao = pyia2.accessibleObjectFromEvent(event)
    print('\n\n===== Document Load Event =====')
    accessible_object_information(ao)

    print('\n----- test Element -----')
    pred = lambda x: pyia2.get_id(x) == 'test'
    ao_test = pyia2.findDescendant(ao, pred)
    if ao_test:
      accessible_object_information(ao_test)
    else:  
        print('Not found')

    print('\n----- myID Element -----')
    pred = lambda x: pyia2.get_id(x) == 'myID'
    ao_myid = pyia2.findDescendant(ao, pred)
    if ao_myid:
      accessible_object_information(ao_myid)
    else:  
        print('Not found')


print("This program monitors document and focus changes events for MSAA and IAccessible2 and provides information about the event.")
event_id = pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE
pyia2.Registry.registerEventListener(event_cb, event_id )

pyia2.Registry.start()