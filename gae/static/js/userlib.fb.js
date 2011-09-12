game.userlib.reloadFriends = function () {
    // init
    FB.init({
        appId  : game.fbAppId,
        status : true, // check login status
        cookie : true, // enable cookies to allow the server to access the session
        xfbml  : true  // parse XFBML
    });

    // resize
    /*
    var obj = new Object;
    obj.width=780;
    obj.height=1350;
    FB.Canvas.setSize(obj);
    */
    FB.Canvas.setAutoResize();

    game.userlib.requestFriends();
}

game.userlib.requestFriends = function () {
    var q = FB.Data.query('SELECT uid FROM user WHERE uid IN '
                + '(SELECT uid2 FROM friend WHERE uid1 = me()) AND is_app_user');

    q.wait(function(resp) {
            var list = [];
            for (var i in resp) {
                list.push(resp[i].uid)
            }
            game.userlib.updateFriends(list);
        }
    );
}

game.userlib.invite = function () {
    FB.ui({
        method: 'apprequests',
        display: 'popup',
        title: 'Пригласи друзей',
        message: 'Классная игрушка "Кубики"! Логическая стратегия, небольшие партии с другими игроками.',
        filters: ['app_non_users'],
        data: 'friends invite'
    });
}

game.userlib.setSettings = function () {
}

game.userlib.scroll = function (loc) {
    var top = (loc=="bottom")
        ? (58 + $('#gamehelpid').position().top)
        : 40;
    FB.Canvas.scrollTo(0, top);
}

game.userlib.resizeWindowHeight = function (h) {
    FB.Canvas.setSize({
        width: 780,
        height: h+10
    });
}

