var app = angular.module('nii', [
    'ui.router',
    'ui.materialize',
]);

app.run(function($rootScope) {
    $rootScope.$on("$stateChangeError", console.log.bind(console));
});


app.config(['$stateProvider', '$urlRouterProvider', 'RestangularProvider',
    function($stateProvider, $urlRouterProvider, RestangularProvider) {

        RestangularProvider.setDefaultHeaders({
            "X-CSRFToken": csrftoken
        });
        $urlRouterProvider.otherwise("/");

        $stateProvider
        	.state("/", {
                url: "/",
                templateUrl: "/static/ng_templates/textbox.html",
                controller: 'EmailUpload'
            })
  	}]);

