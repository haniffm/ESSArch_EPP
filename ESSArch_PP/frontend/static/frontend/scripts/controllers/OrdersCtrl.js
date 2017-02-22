angular.module('myApp').controller('OrdersCtrl', function($scope, $controller, $rootScope) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    vm.displayedIps = [{
        Label: "request",
        Responsible: {username: $rootScope.auth.username},
        CreateDate: new Date(),
        RequestType: "Request type"
    }];

});