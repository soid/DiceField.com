game.userlib.reloadFriends = function () {
    mailru.loader.require('api', function() {
        mailru.connect.init(MM_APP_ID, MM_PRIVATE_KEY);
        game.userlib.requestFriends();
    });
}

game.userlib.requestFriends = function () {
    mailru.common.friends.getAppUsers(function (list) {
        game.userlib.updateFriends(list);
    });
}

game.userlib.invite = function () {
    mailru.app.friends.invite();
}

game.userlib.setSettings = function () {
}

game.userlib.scroll = function (loc) {
    var href = (loc=='bottom') ? 'gamehelpid' : 'game';
    document.location = '#' + href;
}

game.userlib.resizeWindowHeight = function (h) {
    mailru.app.utils.setHeight(h);
}

