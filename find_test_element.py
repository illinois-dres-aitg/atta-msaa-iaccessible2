import pyia2
from pyia2.constants import CHILDID_SELF, \
    UNLOCALIZED_ROLE_NAMES, \
    UNLOCALIZED_STATE_NAMES
from pyia2.utils import IA2Lib
from pyia2.utils import AccessibleDocument

def event_cb(event):
    global doc

    ao = pyia2.accessibleObjectFromEvent(event)
    doc = AccessibleDocument(ao)
    print(doc)


print("This program monitors document change events for MSAA and IAccessible2 and provides information about test elements.")
event_id = pyia2.IA2_EVENT_DOCUMENT_LOAD_COMPLETE
pyia2.Registry.registerEventListener(event_cb, event_id )

pyia2.Registry.start()
