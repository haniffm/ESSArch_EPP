"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Core
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

from ESSArch_Core.storage.models import IOQueue, StorageMedium, StorageObject,  TapeDrive, Robot, StorageMethod, StorageTarget, StorageMethodTargetRelation
from django.contrib import admin
from nested_inline.admin import NestedStackedInline, NestedModelAdmin


class StorageTargetInline(NestedStackedInline):
    """
    StorageTarget configuration
    """        
    model = StorageMethodTargetRelation
    fk_name = 'storage_method'
    extra = 0
    fields = (
        'name',
        'status',
        'storage_target',
        )
    verbose_name = 'target relation'
    verbose_name_plural = ''
    def get_formset(self, request, obj=None, **kwargs):
        formset = super(StorageTargetInline, self).get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields['storage_target'].widget.can_add_related = False
        form.base_fields['storage_target'].widget.can_change_related = False
        return formset


class StorageMethodInline(NestedStackedInline):
    """
    StorageMethod configuration
    """            
    model = StorageMethod
    fk_name = 'archive_policy'
    extra = 0
    fieldsets = (
        (None,{
            'fields': (
                'name',
                'status',
                'type',
                'containers',
                )}),
    )
    inlines = [StorageTargetInline]


class StorageTargetsAdmin( admin.ModelAdmin ):
    """
    StorageTargets configuration
    """    
    list_display = ( 'name', 'target' )
    sortable_field_name = "name"
    fieldsets = (
        (None,{
            'fields': (
                'name',
                'status',
                'type',
                'default_block_size',
                'default_format',
                'min_chunk_size',
                'min_capacity_warning',                
                'max_capacity',
                'remote_server',
                'master_server',
                'target',
                )}),
    )

admin.site.register(StorageTarget, StorageTargetsAdmin)
admin.site.register(Robot)
admin.site.register(TapeDrive)
admin.site.register(IOQueue)
admin.site.register(StorageMedium)
admin.site.register(StorageObject)
