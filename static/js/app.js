var app = angular.module('nii', [
    'ui.router',
    // 'ui.materialize',
    'ngRoute',
]);

app.run(function($rootScope) {
    $rootScope.$on("$stateChangeError", console.log.bind(console));
});


app.config(['$stateProvider', '$urlRouterProvider',
    function($stateProvider, $urlRouterProvider,) {

        // RestangularProvider.setDefaultHeaders({
        //     "X-CSRFToken": csrftoken
        // });
        $urlRouterProvider.otherwise("/");

        $stateProvider
        	.state("/", {
                url: "/",
                templateUrl: "/static/ng_templates/file_upload.html",
                controller: 'EmailUpload'
            })
  	}]);

