'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2016  ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''
try:
    import ESSArch_EPP as epp
except ImportError:
    __version__ = '2'
else:
    __version__ = epp.__version__ 
    
import logging, sys, ESSMSSQL, pytz, uuid, datetime
from essarch.models import storage as storage_old, storageMedium as storageMedium_old, ArchiveObject
from Storage.models import storage, storageMedium
from configuration.models import StorageTargets
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.utils import timezone

import django
django.setup()

logger = logging.getLogger('install')
essConsoleHandler = logging.StreamHandler(sys.stdout)
essConsoleHandler.setLevel(logging.ERROR)
logger.addHandler(essConsoleHandler)

TimeZone = timezone.get_default_timezone_name()
tz=pytz.timezone(TimeZone)

def set_uuid_to_storage():
    storageMedium_objs = storageMedium_old.objects.all()
    for storageMedium_obj in storageMedium_objs:        
        storage_obj_list = storage_old.objects.filter(storageMediumID=storageMedium_obj.storageMediumID).filter(Q(ObjectUUID__isnull=True) | Q(storageMediumUUID__isnull=True))
        for storage_obj in storage_obj_list:
            try:
                if not storage_obj.ObjectUUID:
                    ip_obj = ArchiveObject.objects.get(ObjectIdentifierValue=storage_obj.ObjectIdentifierValue)
                    storage_obj.ObjectUUID = ip_obj
                if not storage_obj.storageMediumUUID:
                    storage_obj.storageMediumUUID = storageMedium_obj
                storage_obj.save()
                logger.info('Update "old" storage: %s, %s, %s, %s with relation to ip_obj' % (ip_obj.ObjectIdentifierValue, 
                                  storage_obj.storageMediumID, 
                                  storage_obj.contentLocationValue,
                                  storage_obj.contentLocationType))     
            except ArchiveObject.DoesNotExist:
                logger.error('ArchiveObject: %s not found!' % storage_obj.ObjectIdentifierValue)
            except storageMedium_old.DoesNotExist:
                logger.error('storageMedium: %s not found!' % storage_obj.storageMediumID)

def migrate_storage_model():
    ArchiveObject_objs = ArchiveObject.objects.all()
    
    for ArchiveObject_obj in ArchiveObject_objs:
        storage_old_objs = ArchiveObject_obj.storage_set.all()
        storage_objs = ArchiveObject_obj.Storage_set.all()
        for storage_old_obj in storage_old_objs:
            storageMedium_old_obj = storage_old_obj.storageMediumUUID
            if not storage_objs.filter(contentLocationType=storage_old_obj.contentLocationType,
                                       contentLocationValue=storage_old_obj.contentLocationValue,
                                       storagemedium__storageMediumID=storageMedium_old_obj.storageMediumID).exists():
                try:
                    storageMedium_obj = storageMedium.objects.get(storageMediumID=storageMedium_old_obj.storageMediumID)
                except storageMedium.DoesNotExist:
                    logger.info('Missing storageMediumID: %s in local "storageMedium" DB, try to insert',storageMedium_old_obj.storageMediumID)
                    try:
                        if storageMedium_old_obj.storageMedium in range(300,330):
                            try:
                                target_obj = StorageTargets.objects.get(target=storageMedium_old_obj.storageMediumID[:3])
                            except ObjectDoesNotExist:
                                try:
                                    target_obj = StorageTargets.objects.get(target=storageMedium_old_obj.storageMediumID[:2])
                                except ObjectDoesNotExist:
                                    target_obj = StorageTargets.objects.get(target=storageMedium_old_obj.storageMediumID[:1])
                        else:
                            target_obj = StorageTargets.objects.get(name=storageMedium_old_obj.storageMediumID)
                    except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
                        logger.error('Target object not found for storageMediumID: %s, error: %s' % (storageMedium_old_obj.storageMediumID, e))
                        logger.error('Failed to migrate storage: %s, %s, %s, %s' % (ArchiveObject_obj.ObjectIdentifierValue, 
                                                      storageMedium_old_obj.storageMediumID, 
                                                      storage_old_obj.contentLocationValue,
                                                      storage_old_obj.contentLocationType))     
                        continue
                    storageMedium_obj = storageMedium()
                    storageMedium_obj.id = storageMedium_old_obj.storageMediumUUID
                    storageMedium_obj.storageMediumUUID = storageMedium_old_obj.storageMediumUUID
                    storageMedium_obj.storageMedium = storageMedium_old_obj.storageMedium
                    storageMedium_obj.storageMediumID = storageMedium_old_obj.storageMediumID
                    storageMedium_obj.storageMediumDate = storageMedium_old_obj.storageMediumDate
                    storageMedium_obj.storageMediumLocation = storageMedium_old_obj.storageMediumLocation
                    storageMedium_obj.storageMediumLocationStatus = storageMedium_old_obj.storageMediumLocationStatus
                    storageMedium_obj.storageMediumBlockSize = storageMedium_old_obj.storageMediumBlockSize
                    storageMedium_obj.storageMediumUsedCapacity = storageMedium_old_obj.storageMediumUsedCapacity
                    storageMedium_obj.storageMediumStatus = storageMedium_old_obj.storageMediumStatus
                    storageMedium_obj.storageMediumFormat = storageMedium_old_obj.storageMediumFormat
                    storageMedium_obj.storageMediumMounts = storageMedium_old_obj.storageMediumMounts
                    storageMedium_obj.linkingAgentIdentifierValue = storageMedium_old_obj.linkingAgentIdentifierValue
                    storageMedium_obj.CreateDate = storageMedium_old_obj.CreateDate
                    storageMedium_obj.CreateAgentIdentifierValue = storageMedium_old_obj.CreateAgentIdentifierValue
                    storageMedium_obj.LocalDBdatetime = storageMedium_old_obj.LocalDBdatetime
                    storageMedium_obj.ExtDBdatetime = storageMedium_old_obj.ExtDBdatetime
                    storageMedium_obj.storagetarget = target_obj
                    storageMedium_obj.save()                          
                logger.info('Missing storage: %s, %s, %s, %s. try to insert' % (ArchiveObject_obj.ObjectIdentifierValue, 
                                                                  storageMedium_obj.storageMediumID, 
                                                                  storage_old_obj.contentLocationValue,
                                                                  storage_old_obj.contentLocationType)) 
                storage_obj = storage()
                storage_obj.contentLocationType = storage_old_obj.contentLocationType
                storage_obj.contentLocationValue = storage_old_obj.contentLocationValue
                storage_obj.LocalDBdatetime = storage_old_obj.LocalDBdatetime
                storage_obj.ExtDBdatetime = storage_old_obj.ExtDBdatetime
                storage_obj.archiveobject = ArchiveObject_obj
                storage_obj.storagemedium = storageMedium_obj
                storage_obj.save()
            else:
                logger.info('Found storage: %s, %s, %s, %s. no need to update' % (ArchiveObject_obj.ObjectIdentifierValue, 
                                                                  storageMedium_old_obj.storageMediumID, 
                                                                  storage_old_obj.contentLocationValue,
                                                                  storage_old_obj.contentLocationType))     

def update_archive_obj_from_ais(ais=True):
    ip_objs=ArchiveObject.objects.filter(Q(DELIVERYTYPE__isnull=True) | Q(ObjectUUID__isnull=True) | Q(ObjectPackageName__isnull=True))
    for ip_obj in ip_objs:
        if ais:
            ip_objs_ext,errno3,why3 = ESSMSSQL.DB().action('IngestObject','GET3',('PolicyId',
                                                                              'ObjectIdentifierValue',
                                                                              'ObjectPackageName',
                                                                              'ObjectSize',
                                                                              'ObjectNumItems',
                                                                              'ObjectMessageDigestAlgorithm',
                                                                              'ObjectMessageDigest',
                                                                              'ObjectPath',
                                                                              'MetaObjectIdentifier',
                                                                              'MetaObjectSize',
                                                                              'CMetaMessageDigestAlgorithm',
                                                                              'CMetaMessageDigest',
                                                                              'PMetaMessageDigestAlgorithm',
                                                                              'PMetaMessageDigest',
                                                                              'DataObjectSize',
                                                                              'DataObjectNumItems',
                                                                              'Status',
                                                                              'StatusActivity',
                                                                              'StatusProcess',
                                                                              'LastEventDate',
                                                                              'linkingAgentIdentifierValue',
                                                                              'CreateDate',
                                                                              'CreateAgentIdentifierValue',
                                                                              'objectGuid',
                                                                              'EntryDate',
                                                                              'EntryAgentIdentifierValue',
                                                                              'OAISPackageType',
                                                                              'preservationLevelValue',
                                                                              'DELIVERYTYPE',
                                                                              'INFORMATIONCLASS',
                                                                              'ObjectActive'),
                                                                             ('ObjectIdentifierValue',ip_obj.ObjectIdentifierValue))
        else:    
            # start - test without centralDB
            ip_objs_ext = []
            if not ip_obj.ObjectUUID: ip_obj.ObjectUUID = str(uuid.uuid4())
            if not ip_obj.ObjectIdentifierValue: ip_obj.ObjectIdentifierValue = ''
            if not ip_obj.ObjectPackageName: ip_obj.ObjectPackageName = ''
            if not ip_obj.ObjectMessageDigest: ip_obj.ObjectMessageDigest = ''
            if not ip_obj.ObjectPath: ip_obj.ObjectPath = ''
            if not ip_obj.MetaObjectIdentifier: ip_obj.MetaObjectIdentifier = ''
            if not ip_obj.CMetaMessageDigest: ip_obj.CMetaMessageDigest = ''
            if not ip_obj.PMetaMessageDigest: ip_obj.PMetaMessageDigest = ''
            if not ip_obj.linkingAgentIdentifierValue: ip_obj.linkingAgentIdentifierValue = ''
            if not ip_obj.CreateAgentIdentifierValue: ip_obj.CreateAgentIdentifierValue = ''
            if not ip_obj.EntryAgentIdentifierValue: ip_obj.EntryAgentIdentifierValue = ''
            if not ip_obj.DELIVERYTYPE: ip_obj.DELIVERYTYPE = ''
            if not ip_obj.OAISPackageType: ip_obj.OAISPackageType = 2
            if not ip_obj.EntryDate: ip_obj.EntryDate = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            ip_obj_ext = [#ip_obj.PolicyId.PolicyID,
                              '99',
                              ip_obj.ObjectIdentifierValue,
                              ip_obj.ObjectPackageName,
                              ip_obj.ObjectSize,
                              ip_obj.ObjectNumItems,
                              ip_obj.ObjectMessageDigestAlgorithm,
                              ip_obj.ObjectMessageDigest,
                              ip_obj.ObjectPath,
                              ip_obj.MetaObjectIdentifier,
                              ip_obj.MetaObjectSize,
                              ip_obj.CMetaMessageDigestAlgorithm,
                              ip_obj.CMetaMessageDigest,
                              ip_obj.PMetaMessageDigestAlgorithm,
                              ip_obj.PMetaMessageDigest,
                              ip_obj.DataObjectSize,
                              ip_obj.DataObjectNumItems,
                              ip_obj.Status,
                              ip_obj.StatusActivity,
                              ip_obj.StatusProcess,
                              ip_obj.LastEventDate,
                              ip_obj.linkingAgentIdentifierValue,
                              ip_obj.CreateDate,
                              ip_obj.CreateAgentIdentifierValue,
                              ip_obj.ObjectUUID,
                              ip_obj.EntryDate,
                              ip_obj.EntryAgentIdentifierValue,
                              ip_obj.OAISPackageType,
                              ip_obj.preservationLevelValue,
                              ip_obj.DELIVERYTYPE,
                              ip_obj.INFORMATIONCLASS,
                              ip_obj.ObjectActive]
            ip_objs_ext.append(ip_obj_ext)
            errno3 = 0
            why3 = ''
            # end - test without centralDB

        if errno3:
            logger.error('Failed to access central DB ' + str(why3))
            continue
        elif len(ip_objs_ext) == 1:
            ip_obj_ext = ip_objs_ext[0]
            logger.debug('IngestObjectUUID: %s' % str(uuid.UUID(ip_obj_ext[23])))
            LastEventDate_dst = ip_obj_ext[19].replace(microsecond=0,tzinfo=tz)
            LastEventDate_utc = LastEventDate_dst.astimezone(pytz.utc)
            CreateDate_dst = ip_obj_ext[21].replace(microsecond=0,tzinfo=tz)
            CreateDate_utc = CreateDate_dst.astimezone(pytz.utc)
            EntryDate_dst = ip_obj_ext[24].replace(microsecond=0,tzinfo=tz)
            EntryDate_utc = EntryDate_dst.astimezone(pytz.utc)

            if ip_obj.check_db_sync(): # Check if ESSArch and centralDB is in sync
                ###################################################
                # archive object exist in local "IngestObject" DB try to update
                logger.info('Found archive object: %s in local "IngestObject" DB, try to update',ip_obj_ext[1])
                timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                timestamp_dst = timestamp_utc.astimezone(tz)
                #ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = ip_obj_ext[0])
                #ip_obj.PolicyId = ArchivePolicy_obj
                ip_obj.ObjectPackageName = ip_obj_ext[2]
                ip_obj.ObjectSize = ip_obj_ext[3]
                ip_obj.ObjectNumItems = ip_obj_ext[4]
                ip_obj.ObjectMessageDigestAlgorithm = ip_obj_ext[5]
                ip_obj.ObjectMessageDigest = ip_obj_ext[6]
                ip_obj.ObjectPath = ip_obj_ext[7]
                ip_obj.MetaObjectIdentifier = ip_obj_ext[8]
                ip_obj.MetaObjectSize = ip_obj_ext[9]
                ip_obj.CMetaMessageDigestAlgorithm = ip_obj_ext[10]
                ip_obj.CMetaMessageDigest = ip_obj_ext[11]
                ip_obj.PMetaMessageDigestAlgorithm = ip_obj_ext[12]
                ip_obj.PMetaMessageDigest = ip_obj_ext[13]
                ip_obj.DataObjectSize = ip_obj_ext[14]
                ip_obj.DataObjectNumItems = ip_obj_ext[15]
                ip_obj.Status = ip_obj_ext[16]
                ip_obj.StatusActivity = ip_obj_ext[17]
                ip_obj.StatusProcess = ip_obj_ext[18]
                ip_obj.LastEventDate = LastEventDate_utc
                ip_obj.linkingAgentIdentifierValue = ip_obj_ext[20]
                ip_obj.CreateDate = CreateDate_utc
                ip_obj.CreateAgentIdentifierValue = ip_obj_ext[22]
                ip_obj.ObjectUUID = uuid.UUID(ip_obj_ext[23])
                ip_obj.EntryDate = EntryDate_utc
                ip_obj.EntryAgentIdentifierValue = ip_obj_ext[25]
                ip_obj.OAISPackageType = ip_obj_ext[26]
                ip_obj.preservationLevelValue = ip_obj_ext[27]
                ip_obj.DELIVERYTYPE = ip_obj_ext[28]
                ip_obj.INFORMATIONCLASS = ip_obj_ext[29]
                ip_obj.ObjectActive = ip_obj_ext[30]
                ip_obj.LocalDBdatetime = timestamp_utc
                ip_obj.ExtDBdatetime = timestamp_utc
                ip_obj.save()
            else:
                logger.error('Local DB and central DB is not in sync for object: %s' % ip_obj.ObjectIdentifierValue)
                continue     
        else:
            logger.error('Problem to get information about object: %s from central DB' % ip_obj.ObjectIdentifierValue)
            continue     

if __name__ == '__main__':
    # Run with old model
    update_archive_obj_from_ais()
    #update_archive_obj_from_ais(ais=False)
    
    ## Run with new model
    #set_uuid_to_storage()
    #migrate_storage_model()       