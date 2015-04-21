angular.module('underscore', []).factory('_', function() {
    return window._;
});

angular.module('ListsApp', ['underscore', 'ui.sortable', 'ngResource'])
    .factory('Lists', function($resource) {
        return $resource('/api/lists/:id', {}, {'query': {method: 'GET', isArray: false }});
    })
    .controller('ListCtrl', ['$scope', 'Lists', '_', function($scope, Lists, _) {
/*
        $scope.lists = [
            {
                id: 1,
                name: 'Todo'
            },
            {
                id: 2,
                name: 'Shopping',
                items: [
                    'eggs',
                    'bacon'
                ]
            }
        ];
*/
        //$scope.lists = Lists.query();
        Lists.query(function (resource) {
            $scope.lists = resource.data;
        });

        $scope.activeListId = null;
        $scope.setActiveList = function(id) {
            if (id !== $scope.activeListId) {
                $scope.activeListId = id;
                $scope.newItem = '';
                $scope.$broadcast('newListSelected');
            }
        };
        $scope.activeList = function() {
            if (!$scope.activeListId) { return {}; }
            var result = $scope.lists.filter(function(element) {
                return element.id === $scope.activeListId;
            });
            return result.length ? result[0] : {};
        };
        $scope.sortableOptions = {
            additionalPlaceholderClass: 'dragged-item'
        };

        $scope.addItemOnEnter = function(event) {
            if (event.keyCode === 13) {
                var newItem = event.currentTarget.value;
                if (newItem) {
                    var items = $scope.activeList().items;
                    if (items) {
                        items.push(newItem);
                    } else {
                        $scope.activeList().items = [newItem];
                    }
                }
                // clear out the preview line
                this.newItem = '';  // 'this' is the current child scope
            }
        };
        $scope.ctrlClickDeleteItem = function(event) {
            if (event.ctrlKey || event.metaKey) {
                $scope.activeList().items = _.without($scope.activeList().items, this.item);
            }
        };

        $scope.createNewList = function() {
            var latestList = _.max($scope.lists, function(list){ return list.id; });
            $scope.lists.push({
                id: latestList.id + 1,
                name: 'New List'
            });
            $scope.setActiveList(latestList.id + 1);
        };
        $scope.deleteActiveList = function() {
            $scope.lists = _.reject($scope.lists, function(list){ return list.id === $scope.activeListId; });
            $scope.activeListId = 0;
        }
    }])
    .directive('focusOn', function($timeout) {
        return {
            restrict: 'A',
            link: function(scope, element, attrs) {
                scope.$on(attrs['focusOn'], function() {
                    $timeout(function() {  // wait till DOM renders the element
                        element.focus();
                        scope.newItem = '';  // clear the newItem model too
                    })
                });
            }
        }
    });
