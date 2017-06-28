angular.module('myApp').factory('Storage', function($http, $q, appConfig) {
    
    // Get storage mediums
    function getStorageMediums(pageNumber, pageSize, filters, sortString, searchString) {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + "storage-mediums/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString
            }
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
    }

    // Get storage objects given storage medium
    function getStorageObjects(pageNumber, pageSize, medium, sortString, searchString) {
        return $http({
            method: 'GET',
            url: medium.url + "storage-objects/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString
            }
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
    }

    // Get tape slots given robot
    function getTapeSlots(robot) {
        return $http.get(robot.url + "tape-slots/").then(function(response) {
            return response.data;
        });
    }

    // Get tape drives
    function getTapeDrives(robot) {
        return $http.get(robot.url + "tape-drives/").then(function(response) {
            return response.data;
        });
    }

    // Get robots
    function getRobots() {
        return $http.get(appConfig.djangoUrl + 'robots/').then(function(response) {
            return response.data;
        });
    }
    return {
        getStorageMediums: getStorageMediums,
        getStorageObjects: getStorageObjects,
        getTapeSlots: getTapeSlots,
        getTapeDrives: getTapeDrives,
        getRobots: getRobots
    }
});