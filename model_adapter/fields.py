from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import loading

def set_rel_target(field, model, field_name):
    # called by contribute_to_class(), this checks to see if we should repoint the
    # related model based on what's in settings
    lookup = '.'.join((model._meta.app_label, model._meta.module_name, field_name))
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
    # called by do_related_class, which is the first point we're
    # guarenteed to have the real model class of the relationship.
    return other

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

