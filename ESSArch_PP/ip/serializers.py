from _version import get_versions

import os

from rest_framework import exceptions, filters, serializers

from ESSArch_Core.configuration.models import EventType

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    EventIP,
    InformationPackage,
    Order,
    Workarea,
)

from ESSArch_Core.profiles.models import SubmissionAgreement

from ESSArch_Core.auth.serializers import UserSerializer
from ESSArch_Core.serializers import DynamicHyperlinkedModelSerializer

from configuration.serializers import ArchivePolicySerializer
from ip.filters import ip_search_fields, InformationPackageFilter

VERSION = get_versions()['version']

class ArchivalInstitutionSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivalInstitution
        fields = ('url', 'id', 'name', 'information_packages',)


class ArchivistOrganizationSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivistOrganization
        fields = ('url', 'id', 'name', 'information_packages',)


class ArchivalTypeSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivalType
        fields = ('url', 'id', 'name', 'information_packages',)


class ArchivalLocationSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivalLocation
        fields = ('url', 'id', 'name', 'information_packages',)


class InformationPackageSerializer(DynamicHyperlinkedModelSerializer):
    responsible = UserSerializer(read_only=True)
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    package_type_display = serializers.SerializerMethodField()
    workarea = serializers.SerializerMethodField()
    aic = serializers.PrimaryKeyRelatedField(queryset=InformationPackage.objects.all())
    first_generation = serializers.SerializerMethodField()
    last_generation = serializers.SerializerMethodField()

    archival_institution = ArchivalInstitutionSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archivist_organization = ArchivistOrganizationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_type = ArchivalTypeSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_location = ArchivalLocationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )

    def get_package_type_display(self, obj):
        return obj.get_package_type_display()

    def get_first_generation(self, obj):
        return obj.is_first_generation()

    def get_last_generation(self, obj):
        return obj.is_last_generation()

    def get_workarea(self, obj):
        workarea = obj.workareas.first()

        if workarea is not None:
            return WorkareaSerializer(workarea, context=self.context).data


    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'label', 'object_identifier_value', 'object_size',
            'package_type', 'package_type_display', 'responsible', 'create_date',
            'entry_date', 'state', 'status', 'step_state',
            'archived', 'cached', 'aic', 'generation', 'archival_institution',
            'archivist_organization', 'archival_type', 'archival_location',
            'policy', 'message_digest', 'message_digest_algorithm', 'workarea',
            'first_generation', 'last_generation', 'start_date', 'end_date',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


class NestedInformationPackageSerializer(DynamicHyperlinkedModelSerializer):
    responsible = UserSerializer(read_only=True)
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    package_type_display = serializers.SerializerMethodField()
    information_packages = serializers.SerializerMethodField()
    submission_agreement = serializers.PrimaryKeyRelatedField(queryset=SubmissionAgreement.objects.all())
    workarea = serializers.SerializerMethodField()
    first_generation = serializers.SerializerMethodField()
    last_generation = serializers.SerializerMethodField()

    search_filter = filters.SearchFilter()

    def get_package_type_display(self, obj):
        return obj.get_package_type_display()

    def get_information_packages(self, obj):
        request = self.context['request']
        view = self.context.get('view')
        view_type = request.query_params.get('view_type', 'aic')

        if view_type == 'ip':
            related = obj.aic.information_packages
        else:
            related = obj.information_packages

        related = related.order_by('generation')

        if view is not None or not getattr(view, 'search_fields', ''):
            view.search_fields = ip_search_fields
            related = self.search_filter.filter_queryset(request, related, view)

        return InformationPackageSerializer(related, many=True, context={'request': request}).data

    def get_workarea(self, obj):
        workarea = obj.workareas.first()

        if workarea is not None:
            return WorkareaSerializer(workarea, context=self.context).data

    archival_institution = ArchivalInstitutionSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archivist_organization = ArchivistOrganizationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_type = ArchivalTypeSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_location = ArchivalLocationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )

    def get_first_generation(self, obj):
        return obj.is_first_generation()

    def get_last_generation(self, obj):
        return obj.is_last_generation()

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'label', 'object_identifier_value', 'package_type', 'package_type_display',
            'responsible', 'create_date', 'entry_date', 'state', 'status',
            'step_state', 'archived', 'cached', 'aic', 'information_packages',
            'generation', 'archival_institution', 'archivist_organization',
            'archival_type', 'archival_location', 'policy', 'message_digest',
            'message_digest_algorithm', 'submission_agreement',
            'submission_agreement_locked', 'workarea',
            'first_generation', 'last_generation', 'start_date', 'end_date',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }

class WorkareaSerializer(serializers.ModelSerializer):
    extracted = serializers.SerializerMethodField()
    packaged = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True, default=serializers.CurrentUserDefault())

    def get_extracted(self, obj):
        return os.path.isdir(obj.path)

    def get_packaged(self, obj):
        return os.path.isfile(obj.path + '.tar')

    class Meta:
        model = Workarea
        fields = (
            'id', 'user', 'ip', 'read_only', 'type',
            'extracted', 'packaged',
        )


class InformationPackageAICSerializer(DynamicHyperlinkedModelSerializer):
    information_packages = InformationPackageSerializer(read_only=True, many=True)
    package_type = serializers.ChoiceField(choices=((1, 'AIC'),))

    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = (
            'id', 'label', 'object_identifier_value',
            'package_type', 'responsible', 'create_date',
            'entry_date', 'information_packages',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


class InformationPackageDetailSerializer(InformationPackageSerializer):
    aic = InformationPackageAICSerializer(omit=['information_packages'])
    policy = ArchivePolicySerializer()
    submission_agreement = serializers.PrimaryKeyRelatedField(queryset=SubmissionAgreement.objects.all())

    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = InformationPackageSerializer.Meta.fields + (
            'tags', 'submission_agreement', 'submission_agreement_locked',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    responsible = UserSerializer(read_only=True,
        default=serializers.CurrentUserDefault()
    )

    information_packages = serializers.HyperlinkedRelatedField(
        many=True, required=False, view_name='informationpackage-detail',
        queryset=InformationPackage.objects.filter(
            package_type=InformationPackage.DIP
        )
    )

    class Meta:
        model = Order
        fields = (
            'url', 'id', 'label', 'responsible', 'information_packages',
        )
