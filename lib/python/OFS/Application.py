##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__='''Application support


$Id: Application.py,v 1.136 2001/01/18 20:40:45 brian Exp $'''
__version__='$Revision: 1.136 $'[11:-2]

import Globals,Folder,os,sys,App.Product, App.ProductRegistry, misc_
import time, traceback, os, string, Products
from string import strip, lower, find, rfind, join
from DateTime import DateTime
from AccessControl.User import UserFolder
from App.ApplicationManager import ApplicationManager
from webdav.NullResource import NullResource
from FindSupport import FindSupport
from urllib import quote
from cStringIO import StringIO
from AccessControl.PermissionRole import PermissionRole
from App.ProductContext import ProductContext
from misc_ import Misc_
import ZDOM
from zLOG import LOG, ERROR, WARNING, INFO
from HelpSys.HelpSys import HelpSys


_standard_error_msg='''\
<dtml-var standard_html_header>

<dtml-if error_message>
 <dtml-var error_message>
<dtml-else>

<TABLE BORDER="0" WIDTH="100%">
<TR VALIGN="TOP">

<TD WIDTH="10%" ALIGN="CENTER">
<IMG SRC="<dtml-var BASE1>/p_/ZButton" ALT="Zope">
</TD>

<TD WIDTH="90%">
  <H2>Zope Error</H2>
  <P>Zope has encountered an error while publishing this resource.
  </P>
  
  <P>
  <STRONG>Error Type: <dtml-var error_type html_quote></STRONG><BR>
  <STRONG>Error Value: <dtml-var error_value html_quote></STRONG><BR> 
  </P>
 
  <HR NOSHADE>
 
  <P>Troubleshooting Suggestions</P>

  <UL>
  <dtml-if "error_type in ('KeyError','NameError')">
  <LI>This resource may be trying to reference a
  nonexistent object or variable <STRONG><dtml-var error_value></STRONG>.</LI>
  </dtml-if>
  <LI>The URL may be incorrect.</LI>
  <LI>The parameters passed to this resource may be incorrect.</LI>
  <LI>A resource that this resource relies on may be encountering an error.</LI>
  </UL>

  <P>For more detailed information about the error, please
  refer to the HTML source for this page.
  </P>

  <P>If the error persists please contact the site maintainer.
  Thank you for your patience.
  </P>
</TD></TR>
</TABLE>

<dtml-comment>
 Here, events like logging and other actions may also be performed, such as
 sending mail automatically to the administrator.
</dtml-comment>

</dtml-if>
<dtml-var standard_html_footer>'''


class Application(Globals.ApplicationDefaultPermissions,
                  ZDOM.Root, Folder.Folder,
                  App.ProductRegistry.ProductRegistry, FindSupport):
    """Top-level system object"""
    title    ='Zope'
    #__roles__=['Manager', 'Anonymous']
    __defined_roles__=('Manager','Anonymous','Owner')
    web__form__method='GET'
    isTopLevelPrincipiaApplicationObject=1
    _isBeingUsedAsAMethod_=0

    # Create the help system object
    HelpSys=HelpSys('HelpSys')

    p_=misc_.p_
    misc_=misc_.misc_

    _reserved_names=('standard_html_header',
                     'standard_html_footer',
                     'standard_error_message',
                     'Control_Panel')

    # This class-default __allow_groups__ ensures that the
    # emergency user can still access the system if the top-level
    # UserFolder is deleted. This is necessary to allow people
    # to replace the top-level UserFolder object.
    
    __allow_groups__=UserFolder()

    def title_and_id(self): return self.title
    def title_or_id(self): return self.title

    def __init__(self):
        # Initialize users
        uf=UserFolder()
        self.__allow_groups__=uf
        self._setObject('acl_users', uf)

        # Initialize control panel
        cpl=ApplicationManager()
        cpl._init()
        self._setObject('Control_Panel', cpl)

        # Note that this may happen before products are
        # installed, so we have to use addDocument as stand-alone.
        import Document
        Document.manage_addDocument(
            self,
            'standard_html_header',
            'Standard Html Header',
            '<HTML><HEAD><TITLE><dtml-var title_or_id>' \
            '</TITLE></HEAD><BODY BGCOLOR="#FFFFFF">')
        Document.manage_addDocument(
            self,
            'standard_html_footer',
            'Standard Html Footer',
            '</BODY></HTML>')
        Document.manage_addDocument(
            self,
            'standard_error_message',
            'Standard Error Message',
            _standard_error_msg)

    def id(self):
        try:    return self.REQUEST['SCRIPT_NAME'][1:]
        except: return self.title

    def __class_init__(self): Globals.default__class_init__(self)

    def PrincipiaRedirect(self,destination,URL1):
        """Utility function to allow user-controlled redirects"""
        if find(destination,'//') >= 0: raise 'Redirect', destination
        raise 'Redirect', ("%s/%s" % (URL1, destination))
    Redirect=ZopeRedirect=PrincipiaRedirect

    def __bobo_traverse__(self, REQUEST, name=None):

        try: return getattr(self, name)
        except AttributeError: pass
        try: return self[name]
        except KeyError: pass
        method=REQUEST.get('REQUEST_METHOD', 'GET')
        if not method in ('GET', 'POST'):
            return NullResource(self, name, REQUEST).__of__(self)

        REQUEST.RESPONSE.notFoundError("%s\n%s" % (name, method))

    def PrincipiaTime(self, *args):
        """Utility function to return current date/time"""
        return apply(DateTime, args)
    ZopeTime=PrincipiaTime

    ZopeAttributionButton__roles__=None
    def ZopeAttributionButton(self):
        """Returns an HTML fragment that displays the 'powered by zope'
        button along with a link to the Zope site."""
        return '<a href="http://www.zope.org/Credits" target="_top"><img ' \
               'src="%s/p_/ZopeButton" width="115" height="50" ' \
               'border="0" alt="Powered by Zope" /></a>' % self.REQUEST.BASE1


    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource object."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Forbidden', 'This resource cannot be deleted.'

    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Forbidden', 'This resource cannot be moved.'
    
    test_url___allow_groups__=None
    test_url=ZopeAttributionButton

    def absolute_url(self, relative=0):
        """Return an absolute url to the object. Note that the url
        will reflect the acquisition path of the object if the object
        has been acquired."""
        if relative: return ''
        return self.aq_acquire('REQUEST')['BASE1']

    def getPhysicalPath(self):
        '''Returns a path that can be used to access this object again
        later, for example in a copy/paste operation.  Designed to
        be used with getPhysicalRoot().
        '''
        # We're at the base of the path.
        return ('',)

    def getPhysicalRoot(self): return self

    checkGlobalRegistry__roles__=()
    def checkGlobalRegistry(self, rebuild=1):
        """Check the global (product) registry for problems, which can
        be caused by disk-based products being deleted and other things
        that Zope cannot know about. If rebuild is true, the global
        registry will be rebuilt automatically if a problem is found.

        The return value will be true if a problem was found (and fixed,
        if rebuild is true). Returns 0 if no problems found."""
        jar=self._p_jar
        zg =jar.root()['ZGlobals']

        result=0
        try:    keys=list(zg.keys())
        except: result=1

        if (not rebuild) or (not result):
            return result
        
        # A problem was found, so try to rebuild the registry. Note
        # that callers should not catch exceptions from this method
        # to ensure that the transaction gets aborted if the registry
        # cannot be rebuilt for some reason.
        LOG('Zope', WARNING, 'Rebuilding global product registry...')
        import BTree
        jar.root()['ZGlobals']=BTree.BTree()
        products=self.Control_Panel.Products
        for product in products.objectValues():
            LOG('Zope', INFO, 'Checking product: %s' % product.id)
            items=list(product.objectItems())
            finished=[]
            idx=0
            while(idx < len(items)):
                name, ob = items[idx]
                base=getattr(ob, 'aq_base', ob)
                if base in finished:
                    idx=idx+1
                    continue
                finished.append(base)
        LOG('Zope', WARNING, 'Successfully rebuilt global product registry')
        return 1
                              


class Expired(Globals.Persistent):
    icon='p_/broken'

    def __setstate__(self, s={}):
        dict=self.__dict__
        if s.has_key('id'):
            dict['id']=s['id']
        elif s.has_key('__name__'):
            dict['id']=s['__name__']
        else: dict['id']='Unknown'
        dict['title']='** Expired **'

    def __save__(self):
        pass

    __inform_commit__=__save__

def initialize(app):
    # Initialize the application

    # Initialize the cache:
    app.Control_Panel.initialize_cache()

    # The following items marked b/c are backward compatibility hacks
    # which make sure that expected system objects are added to the
    # bobobase. This is required because the bobobase in use may pre-
    # date the introduction of certain system objects such as those
    # which provide Lever support.

    # b/c: Ensure that Control Panel exists.
    if not hasattr(app, 'Control_Panel'):
        cpl=ApplicationManager()
        cpl._init()
        app._setObject('Control_Panel', cpl)
        get_transaction().note('Added Control_Panel')
        get_transaction().commit()

    # b/c: Ensure that a ProductFolder exists.
    if not hasattr(app.Control_Panel.aq_base, 'Products'):
        app.Control_Panel.Products=App.Product.ProductFolder()
        get_transaction().note('Added Control_Panel.Products')
        get_transaction().commit()

    # b/c: Ensure that std err msg exists.
    if not hasattr(app, 'standard_error_message'):
        import Document
        Document.manage_addDocument(
            app,
            'standard_error_message',
            'Standard Error Message',
            _standard_error_msg)
        get_transaction().note('Added standard_error_message')
        get_transaction().commit()

    # b/c: Ensure that Owner role exists.
    if hasattr(app, '__ac_roles__') and not ('Owner' in app.__ac_roles__):
        app.__ac_roles__=app.__ac_roles__ + ('Owner',)
        get_transaction().note('Added Owner role')
        get_transaction().commit()

    # Make sure we have Globals
    root=app._p_jar.root()
    if not root.has_key('ZGlobals'):
        import BTree
        app._p_jar.root()['ZGlobals']=BTree.BTree()
        get_transaction().note('Added Globals')
        get_transaction().commit()

    # Install the initial user.
    if hasattr(app, 'acl_users'):
        users = app.acl_users
        if hasattr(users, '_createInitialUser'):
            app.acl_users._createInitialUser()
            get_transaction().note('Created initial user')
            get_transaction().commit()

    install_products(app)

    # Check the global product registry for problems. Note that if the
    # check finds problems but fails to successfully rebuild the global
    # registry we abort the transaction so that we don't leave it in an
    # indeterminate state.
    try:
        if app.checkGlobalRegistry():
            get_transaction().note('Rebuilt global product registry')
            get_transaction().commit()
    except:
         LOG('Zope', ERROR,
             'A problem was found in the global product registry but ' \
             'the attempt to rebuild the registry failed.',
             error=sys.exc_info())
         get_transaction().abort()


def import_products(_st=type('')):
    # Try to import each product, checking for and catching errors.
    path_join=os.path.join
    isdir=os.path.isdir
    exists=os.path.exists
    DictType=type({})
    global_dict=globals()
    silly=('__doc__',)
    modules=sys.modules
    have_module=modules.has_key
    done={}

    for product_dir in Products.__path__:

        product_names=os.listdir(product_dir)
        product_names.sort()

        for product_name in product_names:

            if done.has_key(product_name): continue
            done[product_name]=1

            package_dir=path_join(product_dir, product_name)
            if not isdir(package_dir): continue
            if not exists(path_join(package_dir, '__init__.py')):
                if not exists(path_join(package_dir, '__init__.pyc')):
                    continue

            pname="Products.%s" % product_name
            try:
                product=__import__(pname, global_dict, global_dict, silly)
                if hasattr(product, '__module_aliases__'):
                    for k, v in product.__module_aliases__:
                        if not have_module(k):
                            if type(v) is _st and have_module(v): v=modules[v]
                            modules[k]=v
            except:
                LOG('Zope',ERROR,'Couldn\'t import %s' % pname,
                    error=sys.exc_info())
                f=StringIO()
                traceback.print_exc(100,f)
                f=f.getvalue()
                try: modules[pname].__import_error__=f
                except: pass


def install_products(app):
    # Install a list of products into the basic folder class, so
    # that all folders know about top-level objects, aka products

    path_join=os.path.join
    isdir=os.path.isdir
    exists=os.path.exists
    DictType=type({})

    from Folder import Folder
    folder_permissions={}
    for p in Folder.__ac_permissions__:
        permission, names = p[:2]
        folder_permissions[permission]=names

    meta_types=[]

    global_dict=globals()
    silly=('__doc__',)

    done={}

    get_transaction().note('Prior to product installs')
    get_transaction().commit()

    for product_dir in Products.__path__:

        product_names=os.listdir(product_dir)
        product_names.sort()

        for product_name in product_names:
            # For each product, we will import it and try to call the
            # intialize() method in the product __init__ module. If
            # the method doesnt exist, we put the old-style information
            # together and do a default initialization.
            if done.has_key(product_name):
                continue
            done[product_name]=1

            package_dir=path_join(product_dir, product_name)
            __traceback_info__=product_name
            if not isdir(package_dir): continue
            if not exists(path_join(package_dir, '__init__.py')):
                if not exists(path_join(package_dir, '__init__.pyc')):
                    continue
            try:
                product=__import__("Products.%s" % product_name,
                                   global_dict, global_dict, silly)

                # Install items into the misc_ namespace, used by products
                # and the framework itself to store common static resources
                # like icon images.
                misc_=pgetattr(product, 'misc_', {})
                if misc_:
                    if type(misc_) is DictType:
                        misc_=Misc_(product_name, misc_)
                    Application.misc_.__dict__[product_name]=misc_

                # Here we create a ProductContext object which contains
                # information about the product and provides an interface
                # for registering things like classes and help topics that
                # should be associated with that product. Products are
                # expected to implement a method named 'initialize' in
                # their __init__.py that takes the ProductContext as an
                # argument. 
                productObject=App.Product.initializeProduct(
                    product, product_name, package_dir, app)
                context=ProductContext(productObject, app, product)

                # Look for an 'initialize' method in the product. If it does
                # not exist, then this is an old product that has never been
                # updated. In that case, we will analyze the product and
                # build up enough information to do initialization manually.
                initmethod=pgetattr(product, 'initialize', None)
                if initmethod is not None:
                    initmethod(context)                    

                # Support old-style product metadata. Older products may
                # define attributes to name their permissions, meta_types,
                # constructors, etc.
                permissions={}
                new_permissions={}
                for p in pgetattr(product, '__ac_permissions__', ()):
                    permission, names, default = (
                        tuple(p)+('Manager',))[:3]
                    if names:
                        for name in names:
                            permissions[name]=permission
                    elif not folder_permissions.has_key(permission):
                        new_permissions[permission]=()

                for meta_type in pgetattr(product, 'meta_types', ()):
                    # Modern product initialization via a ProductContext
                    # adds 'product' and 'permission' keys to the meta_type
                    # mapping. We have to add these here for old products.
                    pname=permissions.get(meta_type['action'], None)
                    if pname is not None:
                        meta_type['permission']=pname
                    meta_type['product']=productObject.id
                    meta_types.append(meta_type)

                for name,method in pgetattr(
                    product, 'methods', {}).items():
                    if not hasattr(Folder, name):
                        setattr(Folder, name, method)
                        if name[-9:]!='__roles__': # not Just setting roles
                            if (permissions.has_key(name) and
                                not folder_permissions.has_key(
                                    permissions[name])):
                                permission=permissions[name]
                                if new_permissions.has_key(permission):
                                    new_permissions[permission].append(name)
                                else:
                                    new_permissions[permission]=[name]

                if new_permissions:
                    new_permissions=new_permissions.items()
                    for permission, names in new_permissions:
                        folder_permissions[permission]=names
                    new_permissions.sort()
                    Folder.__dict__['__ac_permissions__']=tuple(
                        list(Folder.__ac_permissions__)+new_permissions)

                if os.environ.get('ZEO_CLIENT',''):
                    # we don't want to install products from clients!
                    get_transaction().abort()
                else:
                    get_transaction().note('Installed product '+product_name)
                    get_transaction().commit()

            except:
                LOG('Zope',ERROR,'Couldn\'t install %s' % product_name,
                    error=sys.exc_info())
                get_transaction().abort()

    Products.meta_types=Products.meta_types+tuple(meta_types)

    Globals.default__class_init__(Folder)


def pgetattr(product, name, default=install_products, __init__=0):
    if not __init__ and hasattr(product, name): return getattr(product, name)
    if hasattr(product, '__init__'):
        product=product.__init__
        if hasattr(product, name): return getattr(product, name)

    if default is not install_products: return default

    raise AttributeError, name
