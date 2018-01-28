"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
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

from django.db.models import (BooleanField, Case, Count, Exists, F,
                              IntegerField, Max, Min, OuterRef, Prefetch, Q,
                              Subquery, Value, When)
from django_filters import rest_framework as filters
from rest_framework import exceptions

from ESSArch_Core.filters import ListFilter
from ESSArch_Core.ip.models import (ArchivalInstitution, ArchivalLocation,
                                    ArchivalType, ArchivistOrganization,
                                    InformationPackage, Workarea)

ip_search_fields = (
    'object_identifier_value', 'label', 'responsible__first_name',
    'responsible__last_name', 'responsible__username', 'state',
    'submission_agreement__name', 'start_date', 'end_date',
)

def get_ip_search_fields():
    with_extra_fields = ip_search_fields

    for field in ip_search_fields:
        with_extra_fields += ('aic__information_packages__%s' % field, 'information_packages__%s' % field)

    return with_extra_fields


class InformationPackageFilter(filters.FilterSet):
    archival_institution = ListFilter(name="archival_institution__name", method='filter_fields')
    archivist_organization = ListFilter(name='archivist_organization__name', method='filter_fields')
    archival_type = ListFilter(name='archival_type__name', method='filter_fields')
    archival_location = ListFilter(name='archival_location__name', method='filter_fields')
    package_type = ListFilter(name='package_type')
    package_type_name_exclude = filters.CharFilter(name='Package Type Name', method='filter_package_type_name')
    state = ListFilter(name='state', method='filter_fields_in_list')
    object_identifier_value = ListFilter(name='object_identifier_value', method='filter_fields')
    label = ListFilter(name='label', method='filter_fields')
    responsible = ListFilter(name='responsible__username', method='filter_fields')
    create_date = ListFilter(name='create_date', method='filter_fields')
    object_size = ListFilter(name='object_size', method='filter_fields')
    start_date = ListFilter(name='Startdate', method='filter_fields')
    end_date = ListFilter(name='Enddate', method='filter_fields')
    archived = filters.BooleanFilter(method='filter_boolean_fields')
    cached = filters.BooleanFilter(method='filter_boolean_fields')

    def __init__(self, *args, **kwargs):
        self.recursive = kwargs.pop('recursive', True)
        super(InformationPackageFilter, self).__init__(*args, **kwargs)

    def prefetch_information_packages(self, qs, ips=None):
        if ips is None:
            information_packages = InformationPackage.objects.filter(
                Q(workareas=None) | Q(workareas__read_only=True)
            )
        else:
            information_packages = ips

        information_packages = information_packages.filter(active=True)

        if self.recursive:
            information_packages = self.__class__(recursive=False, data=self.form.cleaned_data, queryset=information_packages, request=self.request).qs

            if self.form.data.get('view_type', 'aic') == 'aic':
                nested_exists_query = information_packages.filter(aic_id=OuterRef('id'))

        if self.form.data.get('view_type', 'aic') == 'ip':
            field = 'aic__information_packages'
            inner = InformationPackage.objects.filter(aic=OuterRef('aic')).order_by('generation')
            information_packages = information_packages.exclude(generation=Subquery(inner.values('generation')[:1]))
        else:
            field = 'information_packages'

        information_packages = information_packages.select_related('responsible').prefetch_related('workareas', 'steps')

        inner = InformationPackage.objects.annotate(min_gen=Min('generation'), max_gen=Max('generation')).filter(active=True, aic=OuterRef('aic')).order_by('generation')
        information_packages = information_packages.annotate(
            first_generation=Case(
               When(generation=Subquery(inner.values('min_gen')[:1]),
                    then=Value(1)),
               default=Value(0),
               output_field=BooleanField()
            ),
            last_generation=Case(
               When(generation=Subquery(inner.values('max_gen')[:1]),
                    then=Value(1)),
               default=Value(0),
               output_field=BooleanField()
            )
        )

        prefetched = qs.prefetch_related(Prefetch(field, information_packages))

        if self.form.data.get('view_type', 'aic') == 'aic':
            return prefetched.annotate(nested_exists=Exists(nested_exists_query)).filter(
                Q(nested_exists=True) | ~Q(package_type=InformationPackage.AIC)
            )

        return prefetched

    @property
    def qs(self):
        already_prefetched = hasattr(self, '_qs')
        super(InformationPackageFilter, self).qs

        if self.recursive and self.is_bound and not already_prefetched:
            self._qs = self.prefetch_information_packages(self._qs)

        return self._qs

    def filter_package_type_name(self, queryset, name, value):
        for package_type_id, package_type_name in InformationPackage.PACKAGE_TYPE_CHOICES:
            if package_type_name.lower() == value.lower():
                return queryset.exclude(package_type=package_type_id)
        return queryset.none()

    def filter_fields(self, queryset, name, value, lookup=''):
        view_type = self.data.get('view_type', 'aic')

        if lookup:
            lookup = '__%s' % lookup

        if view_type == 'ip':
            related_field = 'aic__information_packages'
        else:
            related_field = 'information_packages'

        return queryset.filter(
            Q(**{'%s%s' % (name, lookup): value}) |
            Q(**{'%s__%s%s' % (related_field, name, lookup): value})
        ).distinct()

    def filter_boolean_fields(self, queryset, name, value):
        return self.filter_fields(queryset, name, value, lookup='exact')

    def filter_fields_in_list(self, queryset, name, value):
        value_list = value.split(u',')
        return self.filter_fields(queryset, name, value_list, lookup='in')


    class Meta:
        model = InformationPackage
        fields = ['package_type', 'package_type_name_exclude', 'state', 'label','object_identifier_value',
        'responsible', 'create_date','object_size', 'start_date', 'end_date',
        'archival_institution', 'archivist_organization']

class WorkareaFilter(InformationPackageFilter):
    type = ListFilter(name='workareas__type', method='filter_workarea')

    def prefetch_information_packages(self, qs):
        user = getattr(self.request, 'user', None)
        information_packages = InformationPackage.objects.select_related('responsible').prefetch_related('steps').all()

        if user is not None and not user.has_perm('ip.see_all_in_workspaces'):
            information_packages = information_packages.filter(workareas__user=user)

        return super(WorkareaFilter, self).prefetch_information_packages(qs, ips=information_packages)

    def filter_workarea(self, queryset, name, value):
        workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

        try:
            workarea_type = workarea_type_reverse[value]
        except KeyError:
            raise exceptions.ParseError('Workarea of type "%s" does not exist' % value)

        return self.filter_fields(queryset, name, workarea_type)

    class Meta:
        model = InformationPackage
        fields = InformationPackageFilter.Meta.fields + ['type']


class ArchivalInstitutionFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__state', distinct=True)

    class Meta:
        model = ArchivalInstitution
        fields = ('ip_state',)


class ArchivistOrganizationFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__state', distinct=True)

    class Meta:
        model = ArchivistOrganization
        fields = ('ip_state',)


class ArchivalTypeFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__state', distinct=True)

    class Meta:
        model = ArchivalType
        fields = ('ip_state',)


class ArchivalLocationFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__state', distinct=True)

    class Meta:
        model = ArchivalLocation
        fields = ('ip_state',)
