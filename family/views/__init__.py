import pkgutil


def setup_views():
    for module_loader, name, ispkg in pkgutil.iter_modules(__path__, prefix='family.views.'):
        __import__(name)
