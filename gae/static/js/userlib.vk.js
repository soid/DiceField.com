game.userlib.reloadFriends = function () {
    VK.init(function () {
        game.userlib.requestFriends();
        VK.addCallback(
            'onSettingsChanged',
            game.userlib.onSettingsChanged);
        VK.callMethod('resizeWindow', 780, 1420);
    });
};

game.userlib.requestFriends = function () {
    if (game.accessFriends) {
        VK.api(
            'friends.getAppUsers',
            {},
            function (r) {
                game.userlib.updateFriends(r.response);
            });
    }
}

game.userlib.invite = function () {
    VK.callMethod('showInviteBox', 2);
}

game.userlib.setSettings = function () {
    VK.callMethod('showSettingsBox', 2);
}

game.userlib.onSettingsChanged = function (api_settings) {
    var af = ((api_settings & 2) == 2);
    game.accessFriends = af;
    game.userlib.requestFriends();
}

game.userlib.scroll = function (loc) {
    var top = (loc=="bottom")
        ? $('#id_openlink').position().top
        : 0;
    VK.callMethod('scrollWindow', 40+top, 700);
}

game.userlib.resizeWindowHeight = function (h) {
    VK.callMethod('resizeWindow', 780, h);
}

