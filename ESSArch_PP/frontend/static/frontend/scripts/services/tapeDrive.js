angular.module('essarch.services').factory('TapeDrive', function($resource, appConfig) {
  return $resource(
    appConfig.djangoUrl + 'tape-drives/:id/:action/',
    {id: '@id'},
    {
      get: {
        method: 'GET',
        params: {id: '@id'},
      },
      query: {
        method: 'GET',
        params: {id: '@id'},
        isArray: true,
        interceptor: {
          response: function(response) {
            response.resource.$httpHeaders = response.headers;
            return response.resource;
          },
        },
      },
      mount: {
        method: 'POST',
        params: {action: 'mount', id: '@id'},
      },
      unmount: {
        method: 'POST',
        params: {action: 'unmount', id: '@id'},
      },
    }
  );
});
