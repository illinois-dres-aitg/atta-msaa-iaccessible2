import pyia2
import inspect
from pyia2.constants import CHILDID_SELF, \
    UNLOCALIZED_ROLE_NAMES, \
    UNLOCALIZED_STATE_NAMES
from pyia2.utils import IA2Lib
from pyia2.utils import AccessibleDocument

doc = False

def event_cb(event):
    global doc

    if event.type == pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE:
        ao = pyia2.accessibleObjectFromEvent(event)
        doc = AccessibleDocument(ao)
        print(doc)
    else:
        if doc:
            if doc.addEvent(event.type):
                doc.updateTestElements()
                print(doc)



print("This program monitors document change events for MSAA and IAccessible2 and provides information about test elements.")

events_array = [pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE, pyia2.EVENT_OBJECT_FOCUS, pyia2.EVENT_OBJECT_STATECHANGE, pyia2.EVENT_OBJECT_SELECTION, pyia2.EVENT_OBJECT_SELECTIONREMOVE, pyia2.EVENT_OBJECT_NAMECHANGE, pyia2.EVENT_OBJECT_DESCRIPTIONCHANGE, pyia2.IA2_EVENT_ACTIVE_DESCENDANT_CHANGED, pyia2.IA2_EVENT_OBJECT_ATTRIBUTE_CHANGED]

for i in events_array:
    pyia2.Registry.registerEventListener(event_cb, i)

# pyia2.Registry.registerEventListener(event_cb, pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE )

# pyia2.Registry.registerEventListener(event_cb, pyia2.EVENT_OBJECT_FOCUS)
# pyia2.Registry.registerEventListener(event_cb, pyia2.EVENT_OBJECT_STATECHANGE)
# pyia2.Registry.registerEventListener(event_cb, pyia2.EVENT_OBJECT_SELECTION)
# pyia2.Registry.registerEventListener(event_cb, pyia2.EVENT_OBJECT_SELECTIONREMOVE)
# pyia2.Registry.registerEventListener(event_cb, pyia2.EVENT_OBJECT_NAMECHANGE)
# pyia2.Registry.registerEventListener(event_cb, pyia2.EVENT_OBJECT_DESCRIPTIONCHANGE)

# pyia2.Registry.registerEventListener(event_cb, pyia2.IA2_EVENT_ACTIVE_DESCENDANT_CHANGED)
# pyia2.Registry.registerEventListener(event_cb, pyia2.IA2_EVENT_OBJECT_ATTRIBUTE_CHANGED)

pyia2.Registry.start()