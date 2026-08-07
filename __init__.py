def classFactory(iface):
    from .plugin import AreaLengthPlugin
    return AreaLengthPlugin(iface)
