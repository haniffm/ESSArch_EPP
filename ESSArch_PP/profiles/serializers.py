from lxml import etree

from rest_framework.exceptions import ValidationError
from rest_framework import serializers

import requests

from ESSArch_Core.essxml.ProfileMaker.models import extensionPackage, templatePackage
from ESSArch_Core.essxml.ProfileMaker.xsdtojson import generateJsonRes

class ProfileMakerExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = extensionPackage
        fields = (
            'id', 'allElements', 'existingElements', 'allAttributes', 'prefix', 'schemaURL', 'targetNamespace',
        )

class ProfileMakerTemplateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        schema_request = requests.get(validated_data['schemaURL'])
        schema_request.raise_for_status()

        schemadoc = etree.fromstring(schema_request.content)
        targetNamespace = schemadoc.get('targetNamespace')
        nsmap = {k: v for k, v in schemadoc.nsmap.iteritems() if k and v != "http://www.w3.org/2001/XMLSchema"}

        try:
            existingElements, allElements = generateJsonRes(schemadoc, validated_data['root_element'], validated_data['prefix']);
        except ValueError as e:
            raise ValidationError(e.message)

        existingElements["root"]["nsmap"] = nsmap

        return templatePackage.objects.create(
            existingElements=existingElements, allElements=allElements,
            targetNamespace=targetNamespace, **validated_data
        )

    class Meta:
        model = templatePackage
        fields = (
            'existingElements', 'allElements', 'name', 'root_element',
            'extensions', 'prefix', 'schemaURL', 'targetNamespace',
        )

        read_only_fields = (
            'existingElements', 'allElements', 'extensions',
        )

        extra_kwargs = {
            'root_element': {
                'required': True
            },
            'targetNamespace': {
                'required': False
            }
        }
