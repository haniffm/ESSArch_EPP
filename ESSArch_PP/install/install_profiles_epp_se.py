#!/usr/bin/env /ESSArch/python27/bin/python
# -*- coding: UTF-8 -*-

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

import json
import os

import django
django.setup()

from django.conf import settings  # noqa

from ESSArch_Core.profiles.models import (  # noqa
    SubmissionAgreement,
    Profile,
)


def installProfiles():
    sa = installSubmissionAgreement()
    installProfileWorkflow(sa)

    installProfileSIP(sa)
    installProfileTransferProject(sa)
    installProfileSubmitDescription(sa)

    installProfileAICDescription(sa)
    installProfileAIP(sa)
    installProfileAIPDescription(sa)
    installProfileDIP(sa)
    installProfilePreservationMetadata(sa)

    # create ERMS SA
    erms_sa_name = "SA National Archive and Government SE (ERMS)"
    try:
        erms_sa = SubmissionAgreement.objects.get(name=erms_sa_name)
    except SubmissionAgreement.DoesNotExist:
        erms_sa = sa
        erms_sa.pk = None
        erms_sa.name = erms_sa_name
        erms_sa.save()

    installProfileContentType(erms_sa)

    return 0


def installSubmissionAgreement():

    dct = {
        'name': 'SA National Archive and Government SE',
        'type': 'Standard',
        'status': 'Agreed',
        'label': 'Submission Agreement National Archive x and Government x',
        'cm_version': '1.0',
        'cm_release_date': '2012-04-26T12:45:00+01:00',
        'cm_change_authority': 'Ozzy Osbourne, NAxx',
        'cm_change_description': 'Original',
        'cm_sections_affected': 'None',
        'producer_organization': 'Government x',
        'producer_main_name': 'Elton John',
        'producer_main_address': 'Bourbon Street 123, City x, Country y',
        'producer_main_phone': '46 (0)8-123450',
        'producer_main_email': 'Elton.John@company.se',
        'producer_main_additional': 'Responsible for contract',
        'producer_individual_name': 'Mike Oldfield',
        'producer_individual_role': 'Archivist',
        'producer_individual_phone': '46 (0)8-123451',
        'producer_individual_email': 'Mike.Oldfield@company.se',
        'producer_individual_additional': 'Principal archivist',
        'archivist_organization': 'National Archive xx',
        'archivist_main_name': 'Ozzy Osbourne',
        'archivist_main_address': 'Main street 123, City x, Country y',
        'archivist_main_phone': '46 (0)8-1001001',
        'archivist_main_email': 'Ozzy.Osbourne@archive.org',
        'archivist_main_additional': 'Responsible for contract',
        'archivist_individual_name': 'Lita Ford',
        'archivist_individual_role': 'Archivist',
        'archivist_individual_phone': '46 (0)8-1001002',
        'archivist_individual_email': 'Lita.Ford@archive.org',
        'archivist_individual_additional': 'Principal archivist',
        'designated_community_description': 'Designated community description',
        'designated_community_individual_name': 'Elvis Presley',
        'designated_community_individual_role': 'Artist',
        'designated_community_individual_phone': '46 (0)8-2002001',
        'designated_community_individual_email': 'Elvis.Presley@xxx.org',
        'designated_community_individual_additional': 'Celebrity',
        'template': [
            {
                "key": "archivist_organization",
                "type": "input",
                "templateOptions": {
                    "type": "text",
                    "required": True,
                    "label": "Archivist Organization"
                },
            }
        ],
    }

    sa, _ = SubmissionAgreement.objects.update_or_create(name=dct['name'], defaults=dct)

    print('Installed submission agreement')

    return sa


def installProfileTransferProject(sa):

    dct = {
        'name': 'Transfer Project Profile SE',
        'profile_type': 'transfer_project',
        'type': 'Implementation',
        'status': 'Agreed',
        'label': 'Transfer Project Profile 1',
        'template': [
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archival institution",
                },
                "type": "input",
                "defaultValue": "Riksarkivet",
                "key": "archival_institution"
            }, {
                "templateOptions": {
                    "type": "text",
                    "disabled": True,
                    "label": "Archivist Organization"
                },
                "type": "input",
                "key": "_IP_ARCHIVIST_ORGANIZATION"
            }, {
                "templateOptions": {
                    "type": "text",
                    "label": "Archival type",
                },
                "type": "input",
                "defaultValue": "document",
                "key": "archival_type"
            }, {
                "templateOptions": {
                    "type": "text",
                    "label": "Archival location",
                },
                "type": "input",
                "defaultValue": "sweden-stockholm-nacka",
                "key": "archival_location"
            }, {
                "templateOptions": {
                    "disabled": True,
                    "type": "text",
                    "label": "Archive Policy ID",
                },
                "type": "input",
                "defaultValue": "1",
                "key": "archive_policy_id"
            }, {
                "templateOptions": {
                    "disabled": True,
                    "type": "text",
                    "label": "Archive Policy Name",
                },
                "type": "input",
                "defaultValue": "default",
                "key": "archive_policy_name"
            }, {
                'key': 'container_format',
                'type': 'select',
                'defaultValue': 'tar',
                'templateOptions': {
                    'label': 'Container format',
                    'options': [
                        {'name': 'TAR', 'value': 'tar'},
                        {'name': 'ZIP', 'value': 'zip'},
                    ]
                }
            }, {
                "key": "container_format_compression",
                "templateOptions": {
                    "label": "Container format compression",
                    "options": [
                        {
                            "name": "Yes",
                            "value": True
                        },
                        {
                            "name": "No",
                            "value": False
                        }
                    ]
                },
                "defaultValue": False,
                "type": "select"
            }, {
                'key': 'checksum_algorithm',
                'type': 'select',
                'defaultValue': 'MD5',
                'templateOptions': {
                    'label': 'Checksum algorithm',
                    'options': [
                        {'name': 'MD5', 'value': 'MD5'},
                        {'name': 'SHA-256', 'value': 'SHA-256'},
                    ]
                }
            }, {
                "templateOptions": {
                    "type": "email",
                    "label": "Preservation organization receiver email",
                },
                "type": "input",
                "key": "preservation_organization_receiver_email"
            }, {
                "templateOptions": {
                    "type": "url",
                    "remote": "",
                    "label": "Preservation organization receiver url (empty for local)",
                },
                "type": "input",
                "key": "preservation_organization_receiver_url"
            }
        ],
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_transfer_project = profile
    sa.save()

    print('Installed profile transfer project')

    return 0


def installProfileSubmitDescription(sa):

    dct = {
        'name': 'Submit description of a single SIP SE',
        'profile_type': 'submit_description',
        'type': 'Implementation',
        'status': 'Draft',
        'label': 'Submit description of a single SIP',
        'template': [
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Start Date"
                },
                "type": "datepicker",
                "defaultValue": "2016-11-10",
                "key": "start_date"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "End Date"
                },
                "type": "datepicker",
                "defaultValue": "2016-12-20",
                "key": "end_date"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "disabled": True,
                    "label": "Archivist Organization"
                },
                "type": "input",
                "key": "_IP_ARCHIVIST_ORGANIZATION"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator"
                },
                "type": "input",
                "defaultValue": "the creator",
                "key": "creator"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Submitter Organization"
                },
                "type": "input",
                "defaultValue": "the submitter organization",
                "key": "submitter_organization"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Submitter Individual"
                },
                "type": "input",
                "defaultValue": "the submitter individual",
                "key": "submitter_individual"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Producer Organization"
                },
                "type": "input",
                "defaultValue": "the producer organization",
                "key": "producer_organization"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Producer Individual"
                },
                "type": "input",
                "defaultValue": "the producer individual",
                "key": "producer_individual"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "IP Owner"
                },
                "type": "input",
                "defaultValue": "the ip owner",
                "key": "ipowner"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Organization"
                },
                "type": "input",
                "defaultValue": "the preservation organization",
                "key": "preservation_organization"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "System Name"
                },
                "type": "input",
                "defaultValue": "the system name",
                "key": "systemname"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "System Version"
                },
                "type": "input",
                "defaultValue": "the system version",
                "key": "systemversion"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "System Type"
                },
                "type": "input",
                "defaultValue": "the system type",
                "key": "systemtype"
            },
        ],
        'specification': json.loads(open(os.path.join(settings.BASE_DIR, 'templates/se/SE_SD_VERSION10.json')).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_submit_description = profile
    sa.save()

    print('Installed profile submit description')

    return 0


def installProfileSIP(sa):

    dct = {
        'name': 'SIP SE',
        'profile_type': 'sip',
        'type': 'Implementation',
        'status': 'Draft',
        'label': 'SIP profile for SE submissions',
        'representation_info': 'Documentation 1',
        'preservation_descriptive_info': 'Documentation 2',
        'supplemental': 'Documentation 3',
        'access_constraints': 'Documentation 4',
        'datamodel_reference': 'Documentation 5',
        'additional': 'Documentation 6',
        'submission_method': 'Electronically',
        'submission_schedule': 'Once',
        'submission_data_inventory': 'According to submit description',
        'structure': [
            {
                'type': 'file',
                'name': 'mets.xml',
                'use': 'mets_file',
            },
            {
                'type': 'folder',
                'name': 'content',
                'use': 'content',
            },
            {
                'type': 'folder',
                'name': 'metadata',
                'use': 'metadata',
                'children': [
                    {
                        'type': 'file',
                        'use': 'xsd_files',
                        'name': 'xsd_files'
                    },
                    {
                        'type': 'file',
                        'name': 'premis.xml',
                        'use': 'preservation_description_file',
                    },
                    {
                        'type': 'file',
                        'name': 'ead.xml',
                        'use': 'archival_description_file',
                    },
                    {
                        'type': 'file',
                        'name': 'eac.xml',
                        'use': 'authoritive_information_file',
                    },
                ]
            },
        ],
        'template': [
            {
                "key": "mets_type",
                "type": "select",
                "defaultValue": "Personnel",
                "templateOptions": {
                    "required": True,
                    "label": "Content Type",
                    "options": [
                        {
                            "name": "Electronic Record Management System",
                            "value": "ERMS"
                        },
                        {
                            "name": "Personnel system",
                            "value": "Personnel"
                        },
                        {
                            "name": "Medical record(s)",
                            "value": "Medical record"
                        },
                        {
                            "name": "Economics",
                            "value": "Economics systems"
                        },
                        {
                            "name": "Databases",
                            "value": "Databases"
                        },
                        {
                            "name": "Webpages",
                            "value": "Webpages"
                        },
                        {
                            "name": "Geografical Information Systems",
                            "value": "GIS"
                        },
                        {
                            "name": "No specification",
                            "value": "No specification"
                        },
                        {
                            "name": "Archival Information Collection",
                            "value": "AIC"
                        },
                        {
                            "name": "Archival Information",
                            "value": "Archival Information"
                        },
                        {
                            "name": "Unstructured",
                            "value": "Unstructured"
                        },
                        {
                            "name": "Single records",
                            "value": "Single records"
                        },
                        {
                            "name": "Publication",
                            "value": "Publication"
                        },
                    ]
                },
            },
            {
                "key": "RECORDSTATUS",
                "type": "select",
                "defaultValue": "NEW",
                "templateOptions": {
                    "label": "Record Status",
                    "options": [
                        {
                            "name": "SUPPLEMENT",
                            "value": "SUPPLEMENT"
                        },
                        {
                            "name": "REPLACEMENT",
                            "value": "REPLACEMENT"
                        },
                        {
                            "name": "NEW",
                            "value": "NEW"
                        },
                        {
                            "name": "TEST",
                            "value": "TEST"
                        },
                        {
                            "name": "VERSION",
                            "value": "VERSION"
                        },
                        {
                            "name": "OTHER",
                            "value": "OTHER"
                        },
                    ]
                },
            },
            {
                "templateOptions": {
                    "type": "text",
                    "disabled": True,
                    "label": "Archivist Organization"
                },
                "type": "input",
                "key": "_IP_ARCHIVIST_ORGANIZATION"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Organization Note"
                },
                "type": "input",
                "defaultValue": "Archivist Organization 1 Note",
                "key": "archivist_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "Creator Organization 1",
                "key": "creator_organization_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization Note"
                },
                "type": "input",
                "defaultValue": "Creator Organization 1 Note",
                "key": "creator_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "archivist_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software Note"
                },
                "type": "input",
                "defaultValue": "Archivist Software 1 Note",
                "key": "archivist_software_note"
            },
            {
                "templateOptions": {
                    "label": "Allow unknown file types",
                    "options": [
                        {"name": "Yes", "value": True},
                        {"name": "No", "value": False},
                    ],
                },
                "type": "select",
                "defaultValue": True,
                "key": "allow_unknown_file_types"
            },
        ],
        'specification': json.loads(open(
            os.path.join(settings.BASE_DIR, 'templates/se/SE_SIP_VERSION11.json')
        ).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_sip = profile
    sa.save()

    print('Installed profile SIP')

    return 0


def installProfileAICDescription(sa):

    dct = {
        'name': 'AIC Description SE',
        'profile_type': 'aic_description',
        'type': 'Implementation',
        'status': 'Draft',
        'label': 'AIC Description profile for SE Packages',
        'representation_info': 'Documentation 1',
        'preservation_descriptive_info': 'Documentation 2',
        'supplemental': 'Documentation 3',
        'access_constraints': 'Documentation 4',
        'datamodel_reference': 'Documentation 5',
        'additional': 'Documentation 6',
        'submission_method': 'Electronically',
        'submission_schedule': 'Once',
        'submission_data_inventory': 'According to submit description',
        'template': [],
        'specification': json.loads(open(
            os.path.join(settings.BASE_DIR, 'templates/se/SE_AIC_DESCRIPTION_VERSION11.json')
        ).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_aic_description = profile
    sa.save()

    print('Installed profile AIC Description')

    return 0


def installProfileAIP(sa):

    dct = {
        'name': 'AIP SE',
        'profile_type': 'aip',
        'type': 'Implementation',
        'status': 'Draft',
        'label': 'AIP profile for SE Packages',
        'representation_info': 'Documentation 1',
        'preservation_descriptive_info': 'Documentation 2',
        'supplemental': 'Documentation 3',
        'access_constraints': 'Documentation 4',
        'datamodel_reference': 'Documentation 5',
        'additional': 'Documentation 6',
        'submission_method': 'Electronically',
        'submission_schedule': 'Once',
        'submission_data_inventory': 'According to submit description',
        'structure': [
            {
                'type': 'file',
                'name': 'mets.xml',
                'use': 'mets_file',
            },
            {
                'type': 'folder',
                'name': 'content',
                'use': 'content',
                'children': [
                    {
                        'type': 'file',
                        'name': 'mets_grp',
                        'use': 'mets_grp',
                    },
                    {
                        'type': 'folder',
                        'name': 'data',
                        'children': [],
                    },
                    {
                        'type': 'folder',
                        'name': 'metadata',
                        'children': [],
                    },
                    {
                        'type': 'folder',
                        'name': '{{INNER_IP_OBJID}}',
                        'use': 'sip',
                        'children': [
                            {
                                'type': 'file',
                                'name': 'metadata.xml',
                                'use': 'content_type_specification'
                            }
                        ],
                    },
                ]
            },
            {
                'type': 'folder',
                'name': 'metadata',
                'use': 'metadata',
                'children': [
                    {
                        'type': 'file',
                        'use': 'xsd_files',
                        'name': 'xsd_files'
                    },
                    {
                        'type': 'file',
                        'name': 'premis.xml',
                        'use': 'preservation_description_file',
                    },
                    {
                        'type': 'file',
                        'name': 'ead.xml',
                        'use': 'archival_description_file',
                    },
                    {
                        'type': 'file',
                        'name': 'eac.xml',
                        'use': 'authoritive_information_file',
                    },
                ]
            },
        ],
        'template': [
            {
                "key": "mets_type",
                "type": "select",
                "defaultValue": "Personnel",
                "templateOptions": {
                    "required": True,
                    "label": "Content Type",
                    "options": [
                        {
                            "name": "Electronic Record Management System",
                            "value": "ERMS"
                        },
                        {
                            "name": "Personnel system",
                            "value": "Personnel"
                        },
                        {
                            "name": "Medical record(s)",
                            "value": "Medical record"
                        },
                        {
                            "name": "Economics",
                            "value": "Economics systems"
                        },
                        {
                            "name": "Databases",
                            "value": "Databases"
                        },
                        {
                            "name": "Webpages",
                            "value": "Webpages"
                        },
                        {
                            "name": "Geografical Information Systems",
                            "value": "GIS"
                        },
                        {
                            "name": "No specification",
                            "value": "No specification"
                        },
                        {
                            "name": "Archival Information Collection",
                            "value": "AIC"
                        },
                        {
                            "name": "Archival Information",
                            "value": "Archival Information"
                        },
                        {
                            "name": "Unstructured",
                            "value": "Unstructured"
                        },
                        {
                            "name": "Single records",
                            "value": "Single records"
                        },
                        {
                            "name": "Publication",
                            "value": "Publication"
                        },
                    ]
                },
            },
            {
                "key": "RECORDSTATUS",
                "type": "select",
                "templateOptions": {
                    "label": "Record Status",
                    "options": [
                        {
                            "name": "SUPPLEMENT",
                            "value": "SUPPLEMENT"
                        },
                        {
                            "name": "REPLACEMENT",
                            "value": "REPLACEMENT"
                        },
                        {
                            "name": "NEW",
                            "value": "NEW"
                        },
                        {
                            "name": "TEST",
                            "value": "TEST"
                        },
                        {
                            "name": "VERSION",
                            "value": "VERSION"
                        },
                        {
                            "name": "OTHER",
                            "value": "OTHER"
                        },
                    ]
                },
            },
            {
                "templateOptions": {
                    "type": "text",
                    "disabled": True,
                    "label": "Archivist Organization"
                },
                "type": "input",
                "key": "_IP_ARCHIVIST_ORGANIZATION"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Organization Note"
                },
                "type": "input",
                "key": "archivist_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "Creator Organization 1",
                "key": "creator_organization_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization Note"
                },
                "type": "input",
                "key": "creator_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "archivist_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software Note"
                },
                "type": "input",
                "key": "archivist_software_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Individual",
                },
                "type": "input",
                "defaultValue": "_PARAMETER_SITE_NAME",
                "key": "creator_individual_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Software",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "ESSArch Preservation Platform",
                "key": "creator_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Software Note",
                },
                "type": "input",
                "defaultValue": "VERSION=3",
                "key": "creator_software_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Organization",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "ES Solutions AB",
                "key": "preservation_organization_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Organization Note",
                },
                "type": "input",
                "defaultValue": "ORG:12345",
                "key": "preservation_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Software",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "ESSArch Preservation Platform",
                "key": "preservation_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Software Note",
                },
                "type": "input",
                "defaultValue": "VERSION=3",
                "key": "preservation_software_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Delivery Type",
                },
                "type": "input",
                "defaultValue": "Delivery Type X",
                "key": "delivery_type"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Delivery Specification",
                },
                "type": "input",
                "defaultValue": "Delivery Specification X",
                "key": "delivery_specification"
            },
            {
                "templateOptions": {
                    "label": "Allow unknown file types",
                    "options": [
                        {"name": "Yes", "value": True},
                        {"name": "No", "value": False},
                    ],
                },
                "type": "select",
                "defaultValue": True,
                "key": "allow_unknown_file_types"
            },
        ],
        'specification': json.loads(open(
            os.path.join(settings.BASE_DIR, 'templates/se/SE_AIP_VERSION11.json')
        ).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_aip = profile
    sa.save()

    print('Installed profile AIP')

    return 0


def installProfileAIPDescription(sa):

    dct = {
        'name': 'AIP Description SE',
        'profile_type': 'aip_description',
        'type': 'Implementation',
        'status': 'Draft',
        'label': 'AIP Description profile for SE Packages',
        'representation_info': 'Documentation 1',
        'preservation_descriptive_info': 'Documentation 2',
        'supplemental': 'Documentation 3',
        'access_constraints': 'Documentation 4',
        'datamodel_reference': 'Documentation 5',
        'additional': 'Documentation 6',
        'submission_method': 'Electronically',
        'submission_schedule': 'Once',
        'submission_data_inventory': 'According to submit description',
        'template': [
            {
                "templateOptions": {
                    "type": "text",
                    "disabled": True,
                    "label": "Archivist Organization"
                },
                "type": "input",
                "key": "_IP_ARCHIVIST_ORGANIZATION"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Organization Note"
                },
                "type": "input",
                "key": "archivist_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "Creator Organization 1",
                "key": "creator_organization_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization Note"
                },
                "type": "input",
                "key": "creator_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "archivist_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software Note"
                },
                "type": "input",
                "key": "archivist_software_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Individual",
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "creator_individual_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Individual Note"
                },
                "type": "input",
                "key": "creator_individual_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Software",
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "creator_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Software Note"
                },
                "type": "input",
                "key": "creator_software_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Organization",
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "preservation_organization_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Organization Note"
                },
                "type": "input",
                "key": "preservation_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Software",
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "preservation_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Preservation Software Note"
                },
                "type": "input",
                "key": "preservation_software_note"
            },
        ],
        'specification': json.loads(open(
            os.path.join(settings.BASE_DIR, 'templates/se/SE_AIP_DESCRIPTION_VERSION11.json')
        ).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_aip_description = profile
    sa.save()

    print('Installed profile AIP Description')

    return 0


def installProfileDIP(sa):

    dct = {
        'name': 'DIP SE',
        'profile_type': 'dip',
        'type': 'Implementation',
        'status': 'Draft',
        'label': 'DIP profile for SE Packages',
        'representation_info': 'Documentation 1',
        'preservation_descriptive_info': 'Documentation 2',
        'supplemental': 'Documentation 3',
        'access_constraints': 'Documentation 4',
        'datamodel_reference': 'Documentation 5',
        'additional': 'Documentation 6',
        'submission_method': 'Electronically',
        'submission_schedule': 'Once',
        'submission_data_inventory': 'According to submit description',
        'template': [
            {
                "key": "mets_type",
                "type": "select",
                "defaultValue": "Personnel",
                "templateOptions": {
                    "required": True,
                    "label": "Content Type",
                    "options": [
                        {
                            "name": "Electronic Record Management System",
                            "value": "ERMS"
                        },
                        {
                            "name": "Personnel system",
                            "value": "Personnel"
                        },
                        {
                            "name": "Medical record(s)",
                            "value": "Medical record"
                        },
                        {
                            "name": "Economics",
                            "value": "Economics systems"
                        },
                        {
                            "name": "Databases",
                            "value": "Databases"
                        },
                        {
                            "name": "Webpages",
                            "value": "Webpages"
                        },
                        {
                            "name": "Geografical Information Systems",
                            "value": "GIS"
                        },
                        {
                            "name": "No specification",
                            "value": "No specification"
                        },
                        {
                            "name": "Archival Information Collection",
                            "value": "AIC"
                        },
                        {
                            "name": "Archival Information",
                            "value": "Archival Information"
                        },
                        {
                            "name": "Unstructured",
                            "value": "Unstructured"
                        },
                        {
                            "name": "Single records",
                            "value": "Single records"
                        },
                        {
                            "name": "Publication",
                            "value": "Publication"
                        },
                    ]
                },
            },
            {
                "key": "RECORDSTATUS",
                "type": "select",
                "templateOptions": {
                    "label": "Record Status",
                    "options": [
                        {
                            "name": "SUPPLEMENT",
                            "value": "SUPPLEMENT"
                        },
                        {
                            "name": "REPLACEMENT",
                            "value": "REPLACEMENT"
                        },
                        {
                            "name": "NEW",
                            "value": "NEW"
                        },
                        {
                            "name": "TEST",
                            "value": "TEST"
                        },
                        {
                            "name": "VERSION",
                            "value": "VERSION"
                        },
                        {
                            "name": "OTHER",
                            "value": "OTHER"
                        },
                    ]
                },
            },
            {
                "templateOptions": {
                    "type": "text",
                    "disabled": True,
                    "label": "Archivist Organization"
                },
                "type": "input",
                "key": "_IP_ARCHIVIST_ORGANIZATION"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Organization Note"
                },
                "type": "input",
                "key": "archivist_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "Creator Organization 1",
                "key": "creator_organization_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Creator Organization Note"
                },
                "type": "input",
                "key": "creator_organization_note"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software",
                    "required": True,
                },
                "type": "input",
                "defaultValue": "ESSArch",
                "key": "archivist_software_name"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Archivist Software Note"
                },
                "type": "input",
                "key": "archivist_software_note"
            },
            {
                "templateOptions": {
                    "label": "Allow unknown file types",
                    "options": [
                        {"name": "Yes", "value": True},
                        {"name": "No", "value": False},
                    ],
                },
                "type": "select",
                "defaultValue": True,
                "key": "allow_unknown_file_types"
            },
        ],
        'specification': json.loads(open(
            os.path.join(settings.BASE_DIR, 'templates/se/SE_DIP_VERSION11.json')
        ).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_dip = profile
    sa.save()

    print('Installed profile DIP')

    return 0


def installProfilePreservationMetadata(sa):

    dct = {
        'name': 'Preservation profile SE',
        'profile_type': 'preservation_metadata',
        'type': 'Implementation',
        'status': 'Draft',
        'label': 'Preservation profile for AIP xxyy',
        'template': [
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Agent Identifier Value"
                },
                "type": "input",
                "defaultValue": "ESSArch_Preservation_Platform",
                "key": "agent_identifier_value"
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": "Agent Name"
                },
                "type": "input",
                "defaultValue": "ESSArch Preservation Platform",
                "key": "agent_name"
            },
            {
                "templateOptions": {
                    "disabled": True,
                    "type": "text",
                    "label": "Container Format"
                },
                "hidden": True,
                "type": "input",
                "key": "$transfer_project__container_format",
            }
        ],
        'specification': json.loads(open(os.path.join(settings.BASE_DIR, 'templates/se/SE_PREMIS.json')).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_preservation_metadata = profile
    sa.save()

    print('Installed profile preservation metadata')

    return 0


def installProfileContentType(sa):

    dct = {
        'name': 'Content Type profile SE (ERMS)',
        'profile_type': 'content_type',
        'type': 'content_type',
        'status': 'Draft',
        'label': 'Content Type profile SE (ERMS)',
        'specification': {
            'name': 'eard_erms'
        }
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_content_type = profile
    sa.save()

    print('Installed profile content type')

    return 0


def installProfileWorkflow(sa):

    dct = {
        'name': 'Workflow SE',
        'profile_type': 'workflow',
        'specification': json.loads(open(os.path.join(settings.BASE_DIR, 'templates/se/SE_WORKFLOW.json')).read()),
    }

    profile, _ = Profile.objects.update_or_create(name=dct['name'], defaults=dct)
    sa.profile_workflow = profile
    sa.save()

    print('Installed profile Workflow')

    return 0


if __name__ == '__main__':
    installProfiles()
