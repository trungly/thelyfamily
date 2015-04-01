angular.module('underscore', []).factory('_', function() {
    return window._; // assumes underscore has already been loaded on the page
});

angular.module('ListsApp', ['underscore'])
    .controller('ListCtrl', function($scope, _) {
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

        $scope.activeListId = null;
        $scope.setActiveList = function(id) {
            $scope.activeListId = id;
            // clear out newItem and focus on it
            //$scope.newItem = '';
        };
        $scope.activeList = function() {
            var result = $scope.lists.filter(function(element) {
                return element.id === $scope.activeListId;
            });
            return result.length ? result[0] : null;
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
                // clear out newItem
                $scope.newItem = '';
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
    })
    .directive('focusOnShow', function() {
        return {
            restrict: 'A',
            link: function(scope, element, attrs) {
                // I can't figure out why, but this doesn't work on the first time we change lists
                var element = element;
                scope.$watch(function() {
                    return scope.activeListId;
                }, function(oldValue, newValue) {
                    element.focus();
                    scope.newItem = '';
                });
            }
        }
    });
