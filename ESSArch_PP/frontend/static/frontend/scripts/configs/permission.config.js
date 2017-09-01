angular.module("permission.config", [])

.constant("permissionConfig", {
	"home": {
		"ingest": {
			"reception": {
				"_permissions": [
					"ip.receive"
				]
			},
			"ipApproval": {
				"_permissions": [
					"ip.preserve",
					"ip.add_to_ingest_workarea",
					"ip.add_to_ingest_workarea_as_new_generation",
					"ip.diff-check"
				]
			},
			"workarea": {
				"_permissions": [
					"ip.move_from_ingest_workarea",
					"ip.preserve_from_ingest_workarea"
				]
			}
		},
		"access": {
			"accessIp": {
				"_permissions": [
					"ip.get_from_storage",
					"ip.get_tar_from_storage",
					"ip.get_from_storage_as_new"
				]
			},
			"workarea": {
				"_permissions": [
					"ip.move_from_access_workarea",
					"ip.preserve_from_access_workarea"
				]
			},
			"createDip": {
				"_permissions": [
					"ip.diff-check",
					"ip.preserve"
				]
			}
		},
		"orders": {
			"_permissions": [
				"ip.prepare_order"
			]
		},
		"management": {},
		"appraisal": {},
		"administration": {
			"mediaInformation": {
				"_permissions": [
					"storage.storage_management"
				]
			},
			"robotInformation": {
				"_permissions": [
					"storage.storage_management"
				]
			},
			"queues": {
				"_permissions": [
					"storage.storage_management"
				]
			},
			"storageMigration": {
				"_permissions": [
					"storage.storage_migration"
				]
			},
			"storageMaintenance": {
				"_permissions": [
					"storage.storage_maintenance"
				]
			},
			"profileManager": {
				"_permissions": [],
				"saEditor": {
					"_permissions": []
				},
				"profileMaker": {
					"_permissions": []
				},
				"import": {
					"_permissions": []
				}
			}
		}
	}
})

;