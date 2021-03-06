angular.module('essarch.language').config(function($translateProvider) {
  $translateProvider.translations('en', {
    ACCESSIP: 'Storage units',
    ADD_ATTRIBUTE: 'Add Attribute',
    ADD_EXTENSION: 'Add extension',
    AIC_DESC: 'AIC for IP',
    APPRAISAL: 'Appraisal',
    APPRAISAL_DATE: 'Appraisal date',
    APPRAISAL_DATE_DESC: 'Appraisal date',
    APPROVAL: 'Approval',
    ARCHIVAL_STORAGE: 'Archival storage',
    ARCHIVED: 'Archived',
    ARCHIVE_POLICY: 'Archive policy',
    AVAILABLE: 'Available',
    BLOCKSIZE: 'Block size',
    CACHED: 'Cached',
    CANCELPRESERVATION: 'Close preservation',
    COLLAPSE_ALL: 'Collapse all',
    CONTENTLOCATION: 'Content location',
    COPYPATH: 'Copy path',
    COULD_NOT_LOAD_PATH: 'Could not load path!',
    CREATEDIP: 'Create dissemination',
    CREATE_TEMPLATE: 'Create template',
    CURRENTMEDIUMID: 'Current medium ID',
    CURRENTMEDIUMPREFIX: 'Current medium prefix',
    DEACTIVATEMEDIA: 'Deactivate media',
    DEACTIVATESTORAGEMEDIUM: 'Deactivate storage medium',
    DESCRIPTION: 'Description',
    DEVICE: 'Device',
    DIFFCHECK: 'Diff-check',
    DIR_EXISTS_IN_DIP: 'Folder with this name already exists!',
    DIR_EXISTS_IN_DIP_DESC:
      'Folder with this name already exists in the dissemination. Do you want to overwrite current folder?',
    DISSEMINATION: 'Dissemination',
    DISSEMINATION_PACKAGES: 'Dissemination packages',
    DO_YOU_WANT_TO_REMOVE_ORDER: 'Do you want to remove order',
    DO_YOU_WANT_TO_REMOVE_TEMPLATE: 'Do you want to remove template?',
    EMAILS_FAILED: 'Emails failed',
    EMAILS_SENT: 'Emails sent',
    ENTERORDERLABEL: 'Enter label for order',
    EXPAND_ALL: 'Expand all',
    FILE_EXISTS_IN_DIP: 'File with this name already exists!',
    FILE_EXISTS_IN_DIP_DESC:
      'File with this name already exists in the dissemination. Do you want to overwrite current file?',
    FORCECOPIES: 'Force additional copies on the same target medium',
    FORMAT: 'Format',
    FORMAT_CONVERSION: 'Format conversion',
    GENERATE_TEMPLATE: 'Generate template',
    GET: 'Get',
    GET_AS_CONTAINER: 'Get as container',
    GET_AS_NEW_GENERATION: 'Get as new generation',
    GLOBALSEARCHDESC_MEDIUM: 'List all storage mediums associated to the search term',
    GLOBALSEARCHDESC_MEDIUM_CONTENT: 'List all medium content associated to the search term',
    GLOBALSEARCHDESC_MIGRATION: 'List all migrations associated to the search term',
    GLOBALSEARCHDESC_ORDER: 'List all orders associated to the search term',
    GLOBALSEARCHDESC_QUEUE: 'List all queue entries associated to the search term',
    GLOBALSEARCHDESC_ROBOT: 'List all robots associated to the search term',
    GLOBALSEARCHDESC_RULE: 'List all rules associated to the search term',
    GLOBALSEARCHDESC_STRUCTURES: 'List all classification structures associated to the search term',
    GLOBALSEARCHDESC_TAPE_DRIVE: 'List all tape drives associated to the search term',
    GLOBALSEARCHDESC_TAPE_SLOT: 'List all tape slots associated to the search term',
    INCLUDE_AIC_XML: 'Include AIC XML',
    INCLUDE_PACKAGE_XML: 'Include package XML',
    INFORMATION_CLASS: 'Information class',
    INGEST: 'Ingest',
    INVENTORY: 'Inventory',
    INVENTORYROBOTS: 'Inventory robots',
    IOQUEUE: 'IO-queue',
    IP_GENERATION: 'IP generation: {{generation}}',
    IP_VIEW_TYPE: 'IP view type',
    LOCATION: 'Location',
    LOCATIONSTATUS: 'Location status',
    LONGTERM_ARCHIVAL_STORAGE: 'Long-term archival storage',
    MATCH_ERROR: 'Information_class in archive policy does not match information_class in ip: ',
    MAXCAPACITY: 'Max capacity',
    MEDIAINFORMATION: 'Media information',
    MEDIA_MIGRATION: 'Media migration',
    MEDIUM: 'Medium',
    MEDIUMCONTENT: 'Medium content',
    MEDIUMID: 'Medium ID',
    MEDIUMPREFIX: 'Medium prefix',
    MISSING_AIC_DESCRIPTION: 'AIC Description profile missing in Submission agreement',
    MISSING_AIP: 'AIP profile missing in Submission agreement',
    MISSING_AIP_DESCRIPTION: 'AIP Description profile missing in Submission agreement',
    MISSING_DIP: 'DIP profile missing in Submission agreement',
    MOUNT: 'Mount',
    MOVE_TO_APPROVAL: 'Move to Approval',
    MOVE_TO_INGEST_APPROVAL: 'Move to Ingest/Approval',
    NEEDTOMIGRATE: 'Need to migrate',
    NEWORDER: 'New order',
    NUMBEROFMOUNTS: 'Number of mounts',
    OBJECTIDENTIFIERVALUE: 'Object identifier value',
    OFFLINE: 'Offline',
    ONLINE: 'Online',
    ORDER: 'Order',
    ORDERS: 'Orders',
    OVERVIEW: 'Overview',
    PACKAGE_TYPE_NAME_EXCLUDE: 'Exclude package type',
    PLACE_IN_CLASSIFICATION_STRUCTURE: 'Place in classification structure',
    POLICYID: 'Policy ID',
    POLICYSTATUS: 'Policy status',
    POSTED: 'Posted',
    PREPAREDIP: 'Prepare dissemination',
    PREPAREDIPDESC: 'Prepare new dissemination',
    PRESERVE: 'Preserve',
    PREVIOUSMEDIUMPREFIX: 'Previous medium prefix',
    PROFILEMAKER: 'Profile maker',
    PROFILEMANAGER: 'Profile manager',
    PUBLIC: 'Public',
    PUBLISH: 'Publish',
    QUEUES: 'Queues',
    READ_ONLY: 'Read only',
    REQUEST: 'Request',
    REQUESTAPPROVED: 'Request approved',
    REQUESTTYPE: 'Request',
    ROBOTINFORMATION: 'Robot information',
    ROBOTQUEUE: 'Robot queue',
    RULES_SAVED: 'Rules saved',
    SAEDITOR: 'SA editor',
    SA_PUBLISHED: 'Submission agreement: {{name}} has been published',
    SEARCH_ADMIN: 'Search',
    SEARCH_ADMINISTRATION: 'Administration for search views',
    SEE_ALL: 'See all',
    SELECTIONLIST: 'Selection list',
    SELECT_ORDERS: 'Select orders ..',
    SELECT_TAGS: 'Select tags ...',
    SETTINGS_SAVED: 'Settings saved',
    STARTMIGRATION: 'Start migration',
    STORAGE: 'Storage',
    STORAGEMAINTENANCE: 'Storage maintenance',
    STORAGEMEDIUM: 'Storage medium',
    STORAGEMIGRATION: 'Storage migration',
    STORAGETARGET: 'Storage target',
    STORAGE_MEDIUMS: 'Storage mediums',
    STORAGE_STATUS: 'Storage status',
    STORAGE_STATUS_DESC: 'Storage status, Archival storage or Long-term archival storage',
    STORAGE_UNIT: 'Storage unit',
    STORAGE_UNITS: 'Storage units',
    TAGS: 'Tags',
    TAPEDRIVES: 'Tape drives',
    TAPELIBRARY: 'Tape library',
    TAPESLOTS: 'Tape slots',
    TARGET: 'Target',
    TARGETNAME: 'Target name',
    TARGETVALUE: 'Target value',
    TARGET_NAME: 'Target name',
    TEMPPATH: 'Temp path',
    TOACCESS: 'to gain access.',
    UNAVAILABLE: 'Unavailable',
    UNMOUNT: 'Unmount',
    UNMOUNT_FORCE: 'Unmount(force)',
    UNSPECIFIED: 'Unspecified',
    USEDCAPACITY: 'Used capacity',
    USE_SELECTED_SA_AS_TEMPLATE: 'Use selected submission agreement as template',
    USE_TEMPLATE: 'Use template',
    WORKING_ON_NEW_GENERATION: '{{username}} is working on a new generation of this IP',
  });
});
