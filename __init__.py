def classFactory(iface):
    from .plugin import AttributeTableShortcutPlugin
    return AttributeTableShortcutPlugin(iface)
