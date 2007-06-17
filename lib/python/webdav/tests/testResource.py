import unittest
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from Acquisition import Implicit

class TestResource(unittest.TestCase):
    def setUp(self):
        self.app = DummyContent()
        self.app.acl_users = DummyUserFolder()
        self._policy = PermissiveSecurityPolicy()
        self._oldPolicy = setSecurityPolicy(self._policy)
        newSecurityManager(None, OmnipotentUser().__of__(self.app.acl_users))

    def tearDown(self):
        noSecurityManager()
        setSecurityPolicy(self._oldPolicy)

    def _getTargetClass(self):
        from webdav.Resource import Resource
        return Resource

    def _makeOne(self):
        klass = self._getTargetClass()
        inst = klass()
        return inst

    def test_z3interfaces(self):
        from webdav.interfaces import IDAVResource
        from webdav.interfaces import IWriteLock
        Resource = self._getTargetClass()
        from zope.interface.verify import verifyClass

        verifyClass(IDAVResource, Resource)
        verifyClass(IWriteLock, Resource)

    def test_MOVE_self_locked(self):
        """
        DAV: litmus"notowner_modify" tests warn during a MOVE request
        because we returned "412 Precondition Failed" instead of "423
        Locked" when the resource attempting to be moved was itself
        locked.  Fixed by changing Resource.Resource.MOVE to raise the
        correct error.
        """
        app = self.app
        request = DummyRequest({}, {})
        response = DummyResponse()
        inst = self._makeOne()
        inst.cb_isMoveable = lambda *arg: True
        inst.restrictedTraverse = lambda *arg: app
        inst.getId = lambda *arg: '123'
        inst._dav_writelocks = {'a':DummyLock()}
        from zope.interface import directlyProvides
        from webdav.interfaces import IWriteLock
        directlyProvides(inst, IWriteLock)
        from webdav.common import Locked
        self.assertRaises(Locked, inst.MOVE, request, response)

    def test_dav__simpleifhandler_cond_put_corrupt_token(self):
        """
        DAV: litmus' cond_put_corrupt_token test (#18) exposed a bug
        in webdav.Resource.dav__simpleifhandler.  If the resource is
        locked at all, and a DAV request contains an If header, and
        none of the lock tokens present in the header match a lock on
        the resource, we need to return a 423 Locked instead of 204 No
        Content.
        """
        ifhdr = 'If: (<locktoken:foo>) (Not <DAV:no-lock>)'
        request = DummyRequest({'URL':'http://example.com/foo/PUT'},
                               {'If':ifhdr})
        response = DummyResponse()
        inst = self._makeOne()
        inst._dav_writelocks = {'a':DummyLock()}
        from zope.interface import directlyProvides
        from webdav.interfaces import IWriteLock
        directlyProvides(inst, IWriteLock)
        from webdav.common import Locked
        self.assertRaises(Locked, inst.dav__simpleifhandler, request, response)

class DummyLock:
    def isValid(self):
        return True

class DummyContent(Implicit):
    def cb_isMoveable(self):
        return True

    def _checkId(self, *arg, **kw):
        return True

    def _verifyObjectPaste(self, *arg):
        return True

class DummyUserFolder(Implicit):
    pass

class DummyRequest:
    def __init__(self, form, headers):
        self.form = form
        self.headers = headers
        
    def get_header(self, name, default):
        return self.headers.get(name, default)

    def get(self, name, default):
        return self.form.get(name, default)

    def __getitem__(self, name):
        return self.form[name]

    def physicalPathFromURL(self, *arg):
        return ['']

class DummyResponse:
    def __init__(self):
        self.headers = {}

    def setHeader(self, name, value, *arg):
        self.headers[name] = value

from AccessControl.PermissionRole import rolesForPermissionOn
from Acquisition import Implicit


class PermissiveSecurityPolicy:
    """
        Very permissive security policy for unit testing purposes.
    """
    #
    #   Standard SecurityPolicy interface
    #
    def validate( self
                , accessed=None
                , container=None
                , name=None
                , value=None
                , context=None
                , roles=None
                , *args
                , **kw):
        if name and name.startswith('hidden'):
            return False
        else:
            return True

    def checkPermission(self, permission, object, context):
        if permission == 'forbidden permission':
            return 0
        if permission == 'addFoo':
            return context.user.allowed(object, ['FooAdder'])
        roles = rolesForPermissionOn(permission, object)
        if isinstance(roles, basestring):
            roles=[roles]
        return context.user.allowed(object, roles)


class OmnipotentUser( Implicit ):
    """
      Omnipotent User for unit testing purposes.
    """
    def getId( self ):
        return 'all_powerful_Oz'

    getUserName = getId

    def getRoles(self):
        return ('Manager',)

    def allowed( self, object, object_roles=None ):
        return 1

    def getRolesInContext(self, object):
        return ('Manager',)

    def _check_context(self, object):
        return True

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestResource),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
