angular.module('essarch.controllers').controller('RemoveNodeModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    $ctrl.data = data;
    $ctrl.node = data.node.original;

    $ctrl.remove = function() {
        Search.removeNode($ctrl.node).then(function(response) {
            Notifications.add($translate.instant('NODE_REMOVED'), 'success');
            $uibModalInstance.close("added");
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        })
    }
    $ctrl.removeFromStructure = function() {
        Search.removeNodeFromStructure($ctrl.node, $ctrl.data.structure.id).then(function(response) {
            Notifications.add($translate.instant('NODE_REMOVED_FROM_STRUCTURE'), 'success');
            $uibModalInstance.close("removed");
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        })
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
})