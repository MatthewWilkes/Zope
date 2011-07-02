##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import Implicit
from App.special_dtml import DTMLFile
from OFS.SimpleItem import Item
from webdav.Lockable import wl_isLocked


class DavLockManager(Item, Implicit):
    id = 'DavLockManager'
    name = title = 'WebDAV Lock Manager'
    meta_type = 'WebDAV Lock Manager'

    security = ClassSecurityInfo()
    security.declareProtected('Manage WebDAV Locks',
                              'findLockedObjects', 'manage_davlocks',
                              'manage_unlockObjects')
    security.declarePrivate('unlockObjects')

    manage_davlocks = manage_main = manage = DTMLFile(
        'dtml/davLockManager', globals())
    manage_davlocks._setName('manage_davlocks')
    manage_options = ({'label': 'Write Locks', 'action': 'manage_main'}, )

    def findLockedObjects(self, frompath=''):
        app = self.getPhysicalRoot()

        if frompath:
            if frompath[0] == '/':
                frompath = frompath[1:]
            # since the above will turn '/' into an empty string, check
            # for truth before chopping a final slash
            if frompath and frompath[-1] == '/':
                frompath= frompath[:-1]

        # Now we traverse to the node specified in the 'frompath' if
        # the user chose to filter the search, and run a ZopeFind with
        # the expression 'wl_isLocked()' to find locked objects.
        obj = app.unrestrictedTraverse(frompath)
        lockedobjs = self._findapply(obj, path=frompath)

        return lockedobjs

    def unlockObjects(self, paths=[]):
        app = self.getPhysicalRoot()

        for path in paths:
            ob = app.unrestrictedTraverse(path)
            ob.wl_clearLocks()

    def manage_unlockObjects(self, paths=[], REQUEST=None):
        " Management screen action to unlock objects. "
        if paths:
            self.unlockObjects(paths)
        if REQUEST is not None:
            m = '%s objects unlocked.' % len(paths)
            return self.manage_davlocks(self, REQUEST, manage_tabs_message=m)

    def _findapply(self, obj, result=None, path=''):
        # recursive function to actually dig through and find the locked
        # objects.

        if result is None:
            result = []
        base = aq_base(obj)
        if not hasattr(base, 'objectItems'):
            return result
        try:
            items = obj.objectItems()
        except Exception:
            return result

        addresult = result.append
        for id, ob in items:
            if path:
                p = '%s/%s' % (path, id)
            else:
                p = id

            dflag = hasattr(ob, '_p_changed') and (ob._p_changed == None)
            bs = aq_base(ob)
            if wl_isLocked(ob):
                li = []
                addlockinfo = li.append
                for token, lock in ob.wl_lockItems():
                    addlockinfo({'owner': lock.getCreatorPath(),
                                 'token': token})
                addresult((p, li))
                dflag = 0
            if hasattr(bs, 'objectItems'):
                self._findapply(ob, result, p)
            if dflag:
                ob._p_deactivate()

        return result

InitializeClass(DavLockManager)
