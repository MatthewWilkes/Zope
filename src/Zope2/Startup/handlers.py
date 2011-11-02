import os
import sys
from re import compile
from socket import gethostbyaddr

# top-level key handlers


# XXX  I suspect there are still problems here.  In most cases, if the
# value is not set from the config file, or if the value is the
# default, the corresponding envvar is not unset, which is needed to
# ensure that the environment variables and the configuration values
# reflect a coherant configuration.

def _setenv(name, value):
    if isinstance(value, str):
        os.environ[name] = value
    else:
        os.environ[name] = `value`

def debug_mode(value):
    value and _setenv('Z_DEBUG_MODE', '1')
    return value

def locale(value):
    import locale
    locale.setlocale(locale.LC_ALL, value)
    return value

def datetime_format(value):
    value and _setenv('DATETIME_FORMAT', value)
    return value

def automatically_quote_dtml_request_data(value):
    not value and _setenv('ZOPE_DTML_REQUEST_AUTOQUOTE', '0')
    return value

def maximum_number_of_session_objects(value):
    default = 1000
    value not in (None, default) and _setenv('ZSESSION_OBJECT_LIMIT', value)
    return value

def session_add_notify_script_path(value):
    value is not None and _setenv('ZSESSION_ADD_NOTIFY', value)
    return value

def session_delete_notify_script_path(value):
    value is not None and _setenv('ZSESSION_DEL_NOTIFY', value)
    return value

def session_timeout_minutes(value):
    default = 20
    value not in (None, default) and _setenv('ZSESSION_TIMEOUT_MINS', value)
    return value

def publisher_profile_file(value):
    value is not None and _setenv('PROFILE_PUBLISHER', value)
    from ZPublisher.Publish import install_profiling
    install_profiling(value)
    return value

def http_realm(value):
    value is not None and _setenv('Z_REALM', value)
    return value

def http_header_max_length(value):
    return value

def enable_ms_public_header(value):
    import webdav
    webdav.enable_ms_public_header = value

# server handlers

def root_handler(config):
    """ Mutate the configuration with defaults and perform
    fixups of values that require knowledge about configuration
    values outside of their context.
    """

    # Set environment variables
    for k,v in config.environment.items():
        os.environ[k] = v

    # Add directories to the pythonpath
    instancelib = os.path.join(config.instancehome, 'lib', 'python')
    if instancelib not in config.path:
        if os.path.isdir(instancelib):
            config.path.append(instancelib)
    path = config.path[:]
    path.reverse()
    for dir in path:
        sys.path.insert(0, dir)

    # Add any product directories not already in Products.__path__.
    # Directories are added in the order they are mentioned

    instanceprod = os.path.join(config.instancehome, 'Products')
    if instanceprod not in config.products:
        if os.path.isdir(instanceprod):
            config.products.append(instanceprod)

    import Products
    L = []
    for d in config.products + Products.__path__:
        if d not in L:
            L.append(d)
    Products.__path__[:] = L

    # set up trusted proxies
    if config.trusted_proxies:
        from ZPublisher import HTTPRequest
        # DM 2004-11-24: added host name mapping (such that examples in
        # conf file really have a chance to work
        mapped = []
        for name in config.trusted_proxies: mapped.extend(_name2Ips(name))
        HTTPRequest.trusted_proxies = tuple(mapped)
    
    # set the maximum number of ConflictError retries
    if config.max_conflict_retries:
        from ZPublisher import HTTPRequest
        HTTPRequest.retry_max_count = config.max_conflict_retries


def handleConfig(config, multihandler):
    handlers = {}
    for name, value in globals().items():
        if not name.startswith('_'):
            handlers[name] = value
    return multihandler(handlers)

# DM 2004-11-24: added
def _name2Ips(host, isIp_=compile(r'(\d+\.){3}').match):
    """Map a name *host* to the sequence of its ip addresses.

    use *host* itself (as sequence) if it already is an ip address.
    Thus, if only a specific interface on a host is trusted,
    identify it by its ip (and not the host name).
    """
    if isIp_(host):
        return [host]
    return gethostbyaddr(host)[2]
