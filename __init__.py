def classFactory(iface):
    from .plugin import AttributeTableFunctionsPlugin
    return AttributeTableFunctionsPlugin(iface)
