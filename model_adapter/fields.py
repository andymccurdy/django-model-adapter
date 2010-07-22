from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import loading

_ADAPTED_MODEL_COUNT = 0

def set_rel_target(field, model, field_name):
    # called by contribute_to_class(), this checks to see if we should repoint the
    # related model based on what's in settings
    lookup = '.'.join((model._meta.app_label, model._meta.object_name, field_name))
    if lookup in settings.ADAPTIVE_MODELS:
        data = settings.ADAPTIVE_MODELS[lookup]
        # data can be a string, which should represent the target related model
        # or i can be a dict with a 'to' key representing the target related model
        if isinstance(data, basestring):
            field.rel.to = data
            field.rel._field_map = {}
        else:
            try:
                field.rel.to = data['to']
            except KeyError:
                raise ImproperlyConfigured("AdaptiveForeignKey (%s) has no 'to' key" % lookup)
            field.rel._field_map = data.get('fields', {})
        field.rel._is_adaptive = True

def get_adapted_model(other, field_map):
    global _ADAPTED_MODEL_COUNT
    # called by do_related_class, which is the first point we're
    # guarenteed to have the real model class of the relationship.
    # build a meta class for the object
    class Meta:
        app_label = other._meta.app_label

    attrs = {'__module__': other.__module__, 'Meta': Meta}
    # add a descriptor for each field mapping
    for attr_name, target_field in field_map.iteritems():
        attrs[attr_name] = AdaptiveDescriptor(attr_name, target_field)
    new_class = type(other._meta.object_name, (other,), attrs)
    # our new class just took over the real classes slot in django's
    # model registry. purge it.
    app_model_registry = loading.cache.app_models[other._meta.app_label]
    del app_model_registry[other._meta.object_name.lower()]
    # and replace it with the original
    loading.register_models(other._meta.app_label, other)
    # and finally, so models validate, register the new class
    # with a unique name inside our own app. we need to do some
    # tricks with the new classes object_name, which is used in
    # the registration process
    obj_name = new_class._meta.object_name
    _ADAPTED_MODEL_COUNT += 1
    new_class._meta.object_name = 'model-%s' % _ADAPTED_MODEL_COUNT
    loading.register_models('model_adapter', new_class)
    new_class._meta.object_name = obj_name
    return new_class

class AdaptiveDescriptor(object):
    def __init__(self, attr_field, target_field):
        self.attr_field = attr_field
        self.target_field = target_field

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        return getattr(instance, self.target_field)

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self.attr_field)
        setattr(instance, self.target_field, value)
            
class AdaptiveForeignKey(models.ForeignKey):
    def contribute_to_class(self, cls, name):
        set_rel_target(self, cls, name)
        super(AdaptiveForeignKey, self).contribute_to_class(cls, name)

    def do_related_class(self, other, cls):
        # at this point, we have the final other model object.
        # if we need to wrap it with our custom class, we can
        if getattr(self.rel, '_is_adaptive', False) and self.rel._field_map:
            self.rel.to = get_adapted_model(other, self.rel._field_map)
        super(AdaptiveForeignKey, self).do_related_class(other, cls)

class AdaptiveOneToOneField(models.OneToOneField):
    def contribute_to_class(self, cls, name):
        set_rel_target(self, cls, name)
        super(AdaptiveOneToOneField, self).contribute_to_class(cls, name)

    def do_related_class(self, other_cls):
        # at this point, we have the final other model object.
        # if we need to wrap it with our custom class, we can
        if getattr(self.rel, '_is_adaptive', False) and self.rel._field_map:
            self.rel.to = get_adapted_model(other, self.rel._field_map)
        super(AdaptiveOneToOneField, self).do_related_class(other, cls)

class AdaptiveManyToManyField(models.ManyToManyField):
    def contribute_to_class(self, cls, name):
        set_rel_target(self, cls, name)
        super(AdaptiveManyToManyField, self).contribute_to_class(cls, name)

    def do_related_class(self, other_cls):
        # at this point, we have the final other model object.
        # if we need to wrap it with our custom class, we can
        if getattr(self.rel, '_is_adaptive', False) and self.rel._field_map:
            self.rel.to = get_adapted_model(other, self.rel._field_map)
        super(AdaptiveManyToManyField, self).do_related_class(other, cls)

