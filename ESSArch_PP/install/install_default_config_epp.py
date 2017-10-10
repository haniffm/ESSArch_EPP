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

import django
django.setup()

from django.contrib.auth.models import User, Group, Permission

from ESSArch_Core.configuration.models import ArchivePolicy, Parameter, Path
from ESSArch_Core.storage.models import (
    DISK,

    StorageMethod,
    StorageMethodTargetRelation,
    StorageTarget,
)


def installDefaultConfiguration():
    print "\nInstalling parameters..."
    installDefaultParameters()

    print "Installing users, groups and permissions..."
    installDefaultUsers()

    print "\nInstalling paths..."
    installDefaultPaths()

    print "\nInstalling archive policies..."
    installDefaultArchivePolicies()

    print "\nInstalling storage methods..."
    installDefaultStorageMethods()

    print "\nInstalling storage targets..."
    installDefaultStorageTargets()

    print "\nInstalling storage method target relations..."
    installDefaultStorageMethodTargetRelations()

    return 0


def installDefaultParameters():
    site_name = 'Site-X'

    dct = {
        'site_name': site_name,
        'medium_location': 'Media_%s' % site_name,
        'content_location_type': 'AIP',
    }

    for key in dct:
        print '-> %s: %s' % (key, dct[key])
        Parameter.objects.get_or_create(entity=key, value=dct[key])

    return 0


def installDefaultUsers():
    user_system, created = User.objects.get_or_create(
        username='system', email='system@essolutions.se',
        is_staff=True, is_superuser=True
    )
    if created:
        user_system.set_password('system')
        user_system.save()

    user_user, created = User.objects.get_or_create(
        username='user', email='usr1@essolutions.se'
    )
    if created:
        user_user.set_password('user')
        user_user.save()

    user_admin, created = User.objects.get_or_create(
        username='admin', email='admin@essolutions.se',
        is_staff=True
    )
    if created:
        user_admin.set_password('admin')
        user_admin.save()

    user_sysadmin, created = User.objects.get_or_create(
        username='sysadmin', email='sysadmin@essolutions.se',
        is_staff=True
    )
    if created:
        user_sysadmin.set_password('sysadmin')
        user_sysadmin.save()

    group_user, _ = Group.objects.get_or_create(name='user')
    group_admin, _ = Group.objects.get_or_create(name='admin')
    group_sysadmin, _ = Group.objects.get_or_create(name='sysadmin')

    permission_list_user = [
        ## ---- app: ip ---- model: informationpackage
        ['can_upload','ip','informationpackage'],                    # Can upload files to IP (Ingest)
        ['delete_informationpackage','ip','informationpackage'], # Can delete Information Package (Ingest)
        ['receive','ip','informationpackage'],                          # Can receive IP (Ingest)
        ['preserve','ip','informationpackage'],                        # Can preserve IP (Ingest)
        ['preserve_dip','ip','informationpackage'],                 # Can preserve DIP (Access)
        ['get_from_storage','ip','informationpackage'],         # Can get extracted IP from storage (Access)
        ['get_tar_from_storage','ip','informationpackage'],   # Can get packaged IP from storage (Access)
        ['get_from_storage_as_new','ip','informationpackage'], # Can get IP "as new" from storage (Access)
        ['add_to_ingest_workarea','ip','informationpackage'],    # Can add IP to ingest workarea "readonly" (Ingest)
        ['add_to_ingest_workarea_as_new','ip','informationpackage'],   # Can add IP as new generation to ingest workarea (Ingest)
        ['diff-check','ip','informationpackage'],                      # Can diff-check IP (?)
        ['receive','ip','informationpackage'],                          # Can receive IP (Ingest)
        ## ---- app: ip ---- model: workarea
        ['move_from_ingest_workarea','ip','workarea'],        # Can move IP from ingest workarea (Ingest)
        ['move_from_access_workarea','ip','workarea'],       # Can move IP from access workarea (Access)        
        ['preserve_from_ingest_workarea','ip','workarea'],   # Can preserve IP from ingest workarea (Ingest)
        ['preserve_from_access_workarea','ip','workarea'],  # Can preserve IP from access workarea (Access)
        ## ---- app: ip ---- model: order
        ['prepare_order','ip','order'],                                        # Can prepare order (Access) 
        ## ---- app: WorkflowEngine ---- model: processtask
        #['can_undo','WorkflowEngine','processtask'],             # Can undo tasks (other)
        #['can_retry','WorkflowEngine','processtask'],             # Can retry tasks (other)
    ]

    for p in permission_list_user:
        p_obj = Permission.objects.get(
                                          codename=p[0], content_type__app_label=p[1],
                                          content_type__model=p[2],
                                          )
        group_user.permissions.add(p_obj)

    permission_list_admin = [
        ## ---- app: ip ---- model: informationpackage
        ['can_upload','ip','informationpackage'],                    # Can upload files to IP (Ingest)
        ['delete_informationpackage','ip','informationpackage'], # Can delete Information Package (Ingest)
        ['receive','ip','informationpackage'],                          # Can receive IP (Ingest)
        ['preserve','ip','informationpackage'],                        # Can preserve IP (Ingest)
        ['preserve_dip','ip','informationpackage'],                 # Can preserve DIP (Access)
        ['get_from_storage','ip','informationpackage'],         # Can get extracted IP from storage (Access)
        ['get_tar_from_storage','ip','informationpackage'],   # Can get packaged IP from storage (Access)
        ['get_from_storage_as_new','ip','informationpackage'], # Can get IP "as new" from storage (Access)
        ['add_to_ingest_workarea','ip','informationpackage'],    # Can add IP to ingest workarea "readonly" (Ingest)
        ['add_to_ingest_workarea_as_new','ip','informationpackage'],   # Can add IP as new generation to ingest workarea (Ingest)
        ['diff-check','ip','informationpackage'],                      # Can diff-check IP (?)
        ['receive','ip','informationpackage'],                          # Can receive IP (Ingest)
        ## ---- app: ip ---- model: workarea
        ['move_from_ingest_workarea','ip','workarea'],        # Can move IP from ingest workarea (Ingest)
        ['move_from_access_workarea','ip','workarea'],       # Can move IP from access workarea (Access)        
        ['preserve_from_ingest_workarea','ip','workarea'],   # Can preserve IP from ingest workarea (Ingest)
        ['preserve_from_access_workarea','ip','workarea'],  # Can preserve IP from access workarea (Access)
        ## ---- app: ip ---- model: order
        ['prepare_order','ip','order'],                                        # Can prepare order (Access) 
        ## ---- app: WorkflowEngine ---- model: processtask
        #['can_undo','WorkflowEngine','processtask'],           # Can undo tasks (other)
        #['can_retry','WorkflowEngine','processtask'],           # Can retry tasks (other)
        ## ---- app: profiles ---- model: profile
        ['add_profile','profiles','profile'],                                  # Can add Profile (Administration)
        ## ---- app: profiles ---- model: submissionagreement
        ['add_submissionagreement','profiles','submissionagreement'], # Can add Submission Agreement (Administration)
        ## ---- app: storage ---- model: storageobject
        ['storage_migration','storage','storageobject'],          # Storage migration (Administration)
        ['storage_maintenance','storage','storageobject'],    # Storage maintenance (Administration)
        ['storage_management','storage','storageobject'],   # Storage management (Administration)        
    ]
   
    for p in permission_list_admin:
        p_obj = Permission.objects.get(
                                          codename=p[0], content_type__app_label=p[1],
                                          content_type__model=p[2],
                                          )        
        group_admin.permissions.add(p_obj)

    permission_list_sysadmin = [
        ## ---- app: auth ---- model: group
        ['add_group','auth','group'],                    # Can add group
        ['change_group','auth','group'],                    # Can change group
        ['delete_group','auth','group'],                    # Can delete group
        ## ---- app: auth ---- model: user
        ['add_user','auth','user'],                    # Can add user
        ['change_user','auth','user'],                    # Can change user
        ['delete_user','auth','user'],                    # Can delete user
        ## ---- app: configuration ---- model: parameter
        ['add_parameter','configuration','parameter'],                    # Can add parameter
        ['change_parameter','configuration','parameter'],                    # Can change parameter
        ['delete_parameter','configuration','parameter'],                    # Can delete parameter
        ## ---- app: configuration ---- model: archivepolicy
        ['add_archivepolicy','configuration','archivepolicy'],                    # Can add archivepolicy
        ['change_archivepolicy','configuration','archivepolicy'],                    # Can change archivepolicy
        ['delete_archivepolicy','configuration','archivepolicy'],                    # Can delete archivepolicy
        ## ---- app: configuration ---- model: path
        ['add_path','configuration','path'],                    # Can add path
        ['change_path','configuration','path'],                    # Can change path
        ['delete_path','configuration','path'],                    # Can delete path
        ## ---- app: configuration ---- model: eventtype
        ['add_eventtype','configuration','eventtype'],                    # Can add eventtype
        ['change_eventtype','configuration','eventtype'],                    # Can change eventtype
        ['delete_eventtype','configuration','eventtype'],                    # Can delete eventtype        
        ## ---- app: profiles ---- model: profile
        ['add_profile','profiles','profile'],                    # Can add profile
        ['change_profile','profiles','profile'],                    # Can change profile
        ['delete_profile','profiles','profile'],                    # Can delete profile
        ## ---- app: profiles ---- model: submissionagreement
        ['add_submissionagreement','profiles','submissionagreement'],                    # Can add submissionagreement
        ['change_submissionagreement','profiles','submissionagreement'],                    # Can change submissionagreement
        ['delete_submissionagreement','profiles','submissionagreement'],                    # Can delete submissionagreement        
        ## ---- app: storage ---- model: storagemethod
        ['add_storagemethod','storage','storagemethod'],                    # Can add storagemethod
        ['change_storagemethod','storage','storagemethod'],                    # Can change storagemethod
        ['delete_storagemethod','storage','storagemethod'],                    # Can delete storagemethod
        ## ---- app: storage ---- model: storagetarget
        ['add_storagetarget','storage','storagetarget'],                    # Can add storagetarget
        ['change_storagetarget','storage','storagetarget'],                    # Can change storagetarget
        ['delete_storagetarget','storage','storagetarget'],                    # Can delete storagetarget
        ## ---- app: storage ---- model: storagemethodtargetrelation
        ['add_storagemethodtargetrelation','storage','storagemethodtargetrelation'],                    # Can add storagemethodtargetrelation
        ['change_storagemethodtargetrelation','storage','storagemethodtargetrelation'],                    # Can change storagemethodtargetrelation
        ['delete_storagemethodtargetrelation','storage','storagemethodtargetrelation'],                    # Can delete storagemethodtargetrelation
        ## ---- app: storage ---- model: storageobject
        ['storage_migration','storage','storageobject'],          # Storage migration (Administration)
        ['storage_maintenance','storage','storageobject'],    # Storage maintenance (Administration)
        ['storage_management','storage','storageobject'],   # Storage management (Administration)        
    ]
   
    for p in permission_list_sysadmin:
        p_obj = Permission.objects.get(
                                          codename=p[0], content_type__app_label=p[1],
                                          content_type__model=p[2],
                                          )        
        group_sysadmin.permissions.add(p_obj)

    group_user.user_set.add(user_user)
    group_admin.user_set.add(user_admin)
    group_sysadmin.user_set.add(user_sysadmin)

    return 0


def installDefaultPaths():
    dct = {
        'path_mimetypes_definitionfile': '/ESSArch/config/mime.types',
        'reception': '/ESSArch/data/gate/reception',
        'ingest': '/ESSArch/data/epp/ingest',
        'cache': '/ESSArch/data/epp/cache',
        'access_workarea': '/ESSArch/data/epp/work',
        'ingest_workarea': '/ESSArch/data/epp/work',
        'disseminations': '/ESSArch/data/epp/disseminations',
        'orders': '/ESSArch/data/epp/orders',
        'verify': '/ESSArch/data/epp/verify',
    }

    for key in dct:
        print '-> %s: %s' % (key, dct[key])
        Path.objects.get_or_create(entity=key, value=dct[key])

    return 0


def installDefaultArchivePolicies():
    cache = Path.objects.get(entity='cache')
    ingest = Path.objects.get(entity='ingest')

    ArchivePolicy.objects.update_or_create(
        policy_name='default',
        defaults={
            'cache_storage': cache, 'ingest_path': ingest,
            'receive_extract_sip': True
        }
    )

    return 0


def installDefaultStorageMethods():
    StorageMethod.objects.get_or_create(
        name='Default Storage Method 1',
        archive_policy=ArchivePolicy.objects.get(policy_name='default'),
        status=True,
        type=DISK,
    )

    return 0


def installDefaultStorageTargets():
    StorageTarget.objects.get_or_create(
        name='Default Storage Target 1',
        status=True,
        type=DISK,
        target=u'/ESSArch/data/store/disk1',
    )

    return 0


def installDefaultStorageMethodTargetRelations():
    StorageMethodTargetRelation.objects.get_or_create(
        name='Default Storage Method Target Relation 1',
        status=True,
        storage_method=StorageMethod.objects.get(name='Default Storage Method 1'),
        storage_target=StorageTarget.objects.get(name='Default Storage Target 1'),
    )

    return 0


if __name__ == '__main__':
    installDefaultConfiguration()
