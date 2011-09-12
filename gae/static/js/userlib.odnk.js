game.userlib.reloadFriends = function () {
    FAPI.init(game.odnkApiServer, game.odnkApiConnection,
    function() {
        //success
        game.userlib.requestFriends();
    }, function(error){
       console.log("Odnoklassniki API initialization failed");
    });
}

function API_callback(method, result, data){
    //console.log("Method "+method+" finished with result "+result+", "+data);
}

game.userlib.requestFriends = function () {
}

game.userlib.invite = function () {
    FAPI.UI.showInvite('Заходи, поиграем в классную игру "Кубики" - логическая игра, где нужно на карте завоевать других игроков.', 'customAttr=customValue');
}

game.userlib.setSettings = function () {
}

game.userlib.scroll = function (loc) {
    var href = (loc=='bottom') ? 'gamehelpid' : 'game';
    document.location = '#' + href;
}

game.userlib.resizeWindowHeight = function (h) {
    h+=30;
    if (h>3000) {
        h = 3000;
    }
    FAPI.UI.setWindowSize(760, h);
}

