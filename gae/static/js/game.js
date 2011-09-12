game = {};

game.yourKey = null;
game.youAre = {}; // array not an object
game.started = false;
game.turn = false;
game.timer = 0;
game.replay = false;
game.isTutorial = false;
game.TIME_ON_TURN = 15

// properties
game.players = {};

game.GSERVER = '';
game.authType = '';

// methods

game.getFlash = function () {
    return swfobject.getObjectById('map_canvas');
}

game.init = function() {
    // friends page
    if (game.accessFriends) {
        $('#tabfriends').html(game.lang('friends_nobody',
            '<a href="#" onClick="game.userlib.invite(); return false;">'));
    } else {
        $('#tabfriends').html(game.lang('friends_no_access',
            '<a href="#" onClick="game.userlib.setSettings(); return false;">'));
    }
}

game.areYouInGame = function () {
    if (game.players[game.yourKey] == undefined) {
        return false;
    } else {
        return true;
    }
}

game.isYourTurn = function () {
    return game.players[game.yourKey] != undefined && game.players[game.yourKey].color == game.turn;
}

game.showHint = function (msg, hint) {
    if (hint == undefined && !game.areYouInGame()) {
        return;
    }
    var div = $('#sysmsgtext');
    div.fadeOut(300, function () {
        div.html(msg);
        div.fadeIn(600);
        game.lastHint = (new Date).getTime();
    });
}

game.lastHint=0;
game.curTip = 0;
game.nextHint = function () {
    var delta = (new Date).getTime() - game.lastHint;
    if (delta < 5000) {
        return;
    }
    var tips = new Array(
        game.lang('hint1'), game.lang('hint2'), game.lang('hint3')
    );
    if (!game.areYouInGame()) {
        tips.unshift(game.lang('hint_start'));
        tips.push(game.lang('hint_freemap'));
    }
    if (game.curTip >= tips.length) {
        game.curTip =0;
    }
    game.showHint(tips[game.curTip], true);
    game.curTip++;
    if (game.curTip>=tips.length) {
        game.curTip = 0;
    }
}

game.getColorName = function (id, cs) {
    if (cs==null) {
        var words = lang.colors;
    }
    return words[id];
}

game.fUpper = function (str) {
    return str.slice(0,1).toUpperCase() + str.slice(1)
}

game.onCellClick = function (id, yours) {
    if (!game.areYouInGame()) {
        if (game.started) {
            game.showHint(game.lang('hint_click'), true)
        } else {
            game.showHint(game.lang('hint_click_started'), true)
        }
    } else {
        if (!game.started) {
            game.showHint(game.lang('hint_click_wait'), true)
        } else if (!game.isYourTurn()) {
            game.showHint(game.lang('hint_click_wrong_turn', game.getColorName(game.turn)), true)
        }
    }
}

game.onBtnHelp = function () {
    if (game.authType == 'guest') {
        game.openLink('/help.html');
    } else {
        game.openLink('/help.html?type=mm');
    }
}

game.openLink = function (link) {
    var where = 'openlink';
    if (game.authType == 'guest' || game.replay) {
        where = '_blank';
    } else {
        // open in iframe
        game.userlib.scroll('bottom');
        $("#id_openlink").css('opacity', '0.25');
    }
    var nw = window.open(link, where);
    nw.focus();
    if (game.authType != 'guest') {
        $('#id_openlink').load(function () {
            var plus = 30;
            if (game.authType == 'odnk') {
                plus = 60;
            }
            document.getElementById('id_openlink').height
                = $(document.getElementById('id_openlink').contentWindow.document.body).outerHeight() + plus;
            game.userlib.resizeWindowHeight(
                $(document.getElementById('id_openlink')).position().top
                + $(document.getElementById('id_openlink').contentWindow.document.body).outerHeight() 
                + 70 // back button
                );
        });
    }
    return false;
}

game.openLinkReady = function () {
    if (game.authType == 'guest' || game.replay) {
    } else {
        // in iframe
        $("#id_openlink").css('opacity', '1');
    }
}

// Chat
game.chat = {}

game.chat.msgCount = 0;
game.chat.displayMsg = function (message, addTime) {
    var chat = $('#chat');
    if (addTime) {
        var d = new Date();
        var min = d.getMinutes();
        message = '<font color="#AAAAAA">.' + min + '</font> ' + message;
    }
    var tmp = '<div class="chtmsg">' + message + '</div>' + chat.html();
    chat.html(tmp);
    game.chat.msgCount++;

    if (game.chat.msgCount>1000) {
        $('.chtmsg:gt(1000)').remove();
    }
    
    //chat.scrollTop = chat.scrollHeight - chat.offsetHeight;
}

game.chat.sendInput = function () {
    var input = document.getElementById('chat_cl');
    game.getFlash().sendChatMessage(input.value);
    input.value = '';
}

game.chat.onSysMessage = function (data) {
    var type = data[0];
    if (type == 1) {
        // can't play with
        game.chat.displayMsg('<font color="red">' + game.lang('sys_ban_together') + ' '
            + escapeHTML(data[1]['name']) + '</font>');
    } else if (type == 2) {
        // can't write in chat
        game.chat.displayMsg('<font color="red">' + game.lang('sys_ban_chat') + '.</font>');
    } else if (type == 'ban_chat') {
        // ban for player
        game.chat.displayMsg('<font color="red">'
            + game.lang('sys_ban_chat_notice', escapeHTML(data[1]['name'])) + '</font>');
        var p = game.getPlayerByKey(data[1]['key']);
        if (p) {
            p.banChat = true;
            game.updatePlayersList();
        }
    } else if (type == 'ban_score') {
        // ban for player
        game.chat.displayMsg('<font color="red">'
            + game.lang('sys_ban_score_notice', escapeHTML(data[1]['name']), data[2])
            + '</font>');
    } else if (type == 'new_season') {
        game.chat.displayMsg('<font color="green">' + game.lang('sys_new_season') + '</font>');
        for (var key in game.players) {
            game.players[key].score = 0;
        }
        game.updatePlayersList();
    } else if (type == 'same_ip_err') {
        var msg = game.lang('sys_ip_err');
        var nicks = [];
        for (var i in data[1]) {
            nicks.push(escapeHTML(data[1][i]['name']));
        }
        if (nicks.length==1) {
            msg += game.lang('sys_ip_err_p1') + escapeHTML(nicks[0]);
            msg += '. ' + game.lang('sys_ip_err_t68');
        } else if (nicks.length > 1) {
            msg += game.lang('sys_ip_err_pm');
            msg += nicks.join(", ");
            if (nicks.length == 2) {
                msg += '. ' ;
            }
        }
        game.chat.displayMsg('<font color="red">' + msg + '.</font>');
    } else if (type == 'same_ip_err_guest') {
        var msg = game.lang('sys_guest_1', escapeHTML(data[1]['name']));
        game.chat.displayMsg('<font color="red">' + msg + '.</font>');
    } else if (type == 'same_ip_err_guest2') {
        var msg = game.lang('sys_guest_2', escapeHTML(data[1]['name']));
        game.chat.displayMsg('<font color="red">' + msg + '.</font>');
    } else if (type == 'shutdown') {
        var msg = game.lang('sys_shutdown');
        game.chat.displayMsg('<font color="red">' + msg + '.</font>');
    }
}

game.chat.onMessage = function (data) {
    game.chat.displayMsg(
        '<b><a href="/user/' + data[0] + '" onClick="return game.openLink(\'/user/'
        + data[0] + '\');" class="color' + data[2] + '">'
        + escapeHTML(game.getNickByPar(data[1], data[4])) + '</a></b>: '
        + escapeHTML(data[3])
    , true);
}
game.sysBoard = function (html) {
    var e = $('#tabturns');
    e.html('<div class="trnmsg">' + html + '</div>' + e.html());
    $('.trnmsg:gt(200)').remove();
}
game.makePhoto = function (p, width) {
    var photo = '<div style="clip:rect(0px, ' + width + 'px, ' + width + 'px, 0px);position:relative;">'
        + '<a href="' + p.link + '" onClick="return game.openLink(\'' + p.link + '\');">'
        + '<img border="0" src="' + (p.photo?p.photo:'/images/avatar_male.png') + '" width="36"/></a></div>';
    return photo;
}

game.makeA = function (url, title) {
    return '<a href=' + url + '" onClick="return game.openLink(\'' + url + '\');">' + title + '</a>';
}

game.updateTop = function () {
    $.ajax({
		async: true,
		cache: false,
		url: game.GSERVER + '/rating/top.json',
		type: 'GET',
		data: {},
		dataType: 'json',
		success: function (data) {
			var top = $('#top');
            var html = '';
            html += '<table border="0">';
            for (var i in data) {
                var u = data[i];
                html += '<tr><td>' + u.score + '</td><td>';
                html += game.makePhoto(u, 28) + '</td><td>' + escapeHTML(game.getNickByPlArr(u));
                html += '</td></tr>';
            }
            html += '</table>';
            if (data==null || data.length==0) {
                html = game.lang('top_no_games');
            }
            top.html(html);
        },
		error: function (XMLHttpRequest, textStatus, errorThrown) {
		}
	});
}

game.userlib = {}
game.userlib.friends = {}

game.userlib.updateFriendsChunk = function(c) {
    $.post('/vkontakte/friends.html', {'ids': c, 'type': game.authType}, function (data) {
        for (var j in data) {
            var u = data[j];
            game.userlib.friends[u.link] = u;
        }
        game.updateFriends();
    }, 'json');
}

game.userlib.updateFriends = function (ids) {
    var chunk = [];
    var delay = 0;
    var j = 1;
    for (var i in ids) {
        chunk.push(ids[i]);
        if (j % 20 == 0) {
            setTimeout('game.userlib.updateFriendsChunk("' + chunk.join(",") + '")', delay);
            delay += 1 * 1000;
            chunk = [];
        }
        j++;
    }
    if (chunk) {
        game.userlib.updateFriendsChunk(chunk.join(","));
    }
}

game.updateFriends = function () {
    var tab = $('#tabfriends');
    var html = '<table border="0">';
    var len = 0;
    var sorted_friends = [];
    for (var l in game.userlib.friends) {
        sorted_friends.push(game.userlib.friends[l]);
    }
    function sortScore(a,b) {
        return b.score - a.score;
    }
    var sorted_friends_ = sorted_friends.sort(sortScore);
    sorted_friends = sorted_friends_;
    
    for (var i in sorted_friends) {
        var u = sorted_friends[i];
        html += '<tr><td>' + u.score + '</td><td>';
        html += game.makePhoto(u, 28) + '</td><td>' + escapeHTML(lang.romanize(u.name));
        html += '</td></tr>';
        len++;
    }
    html += '</table>';
    html += '<a href="#" onClick="game.userlib.invite(); return false;">' + game.lang('friends_invite_more') + '</a>';
    if (len==0) {
        html = game.lang('friends_nobody',
            '<a href="#" onClick="game.userlib.invite(); return false;">');
    }
    tab.html(html);
}

// Map
game.map = {};
game.map.bid = 0;
game.map.max_players = 0;
game.map.max_score = 0;

// Players
game.players = {};
game.color2player = {};
game.addPlayer = function (arr) {
    var player = new game.CPlayer()
    player.key = arr['key'];
    if (player.key == game.yourKey) {
        game.youAre = arr;
    }
    player.name = arr['name'];
    player.color = arr['color'];
    player.photo = arr['photo'] ? arr['photo']:'/images/avatar_male.png';
    player.link = arr['link'];
    player.score = arr['score'];
    player.depot = arr['depot'];
    player.cellsCount = 0;
    player.away = arr['away'];
    player.banChat = arr['banChat'];
    player.country = arr['country'];
    player.location = arr['location'];
    player.type = arr['t'];
    game.players[player.key] = player;
    game.color2player[player.color] = player;
    game.updatePlayersList();
}
game.onPlayersLoad = function (data) {
    game.players = {};
    game.color2player = {};
    $(data).each(function (i, p) {
        game.addPlayer(p)
    });
    game.started = false;
    game.updatePlayersList();
}
game.onPlayerComing = function (data) {
    if (data['key'] == game.yourKey) {
        game.youAre = data;
    } else {
        game.chat.displayMsg('<font color="#ABABAB">'
            + game.lang('chat_coming', escapeHTML(game.getNickByPlArr(data))) + '.</font>');
    }
}
game.onPlayerLeave = function (pl) {
    game.chat.displayMsg('<font color="#ABABAB">' + game.lang('chat_leaving', escapeHTML(game.getNickByPlArr(pl))) + '.</font>');
}
game.onPlayerGoesRoom = function (params) {
    game.chat.displayMsg('<font color="#ABABAB">'
        + game.lang('chat_moving', escapeHTML(game.getNickByPlArr(params[0])), params[1]['title'])
        + '.</font>');
}
game.onSit = function (data) {
    game.addPlayer(data);
}
game.onGoesAway = function (player) {
    game.players[player.key].away = true;
    game.updatePlayersList();
}
game.onComeBack = function (player) {
    game.players[player.key].away = false;
    game.updatePlayersList();
}
game.onStandUp = function (player) {
    game.players[player.key].rm();
    game.updatePlayersList();
}
game.onMap = function (bid, max_players, max_score) {
    game.map.bid = bid;
    game.map.max_players = max_players;
    game.map.max_score = max_score;
    for (var i=0; i<8; i++) {
        $('div#divTimer' + i).css('visibility', 'hidden');
    }
    if (max_players<=4) {
        $('table#secondRow').hide();
    } else {
        $('table#secondRow').show();
    }
    for (var i=0; i<game.map.max_players; i++) {
        var si = i;
        if (game.map.max_players == 6) {
            if (i==4) {
                $('td#slot4').html('');
                si=5;
            }
            if (i==5) {
                $('td#slot7').html('');
                si=6;
            }
        }
        $('td#slot' + si).html('<div id="player' + i + '" class="player' + i + '"></div>'
            + '<div id="divTimer' + i + '" style="visibility: hidden;" class="timer"></div>');
    }
    if (game.map.max_players > 4) {
        $('div#player' + (game.map.max_players -1)).addClass('playercornertopright');
    }
}
game.onPowerMap = function (pmap) {
    game.started = true;
    var sums = {};
    for (var i in pmap) {
        if (sums[pmap[i][0]] == undefined) {
            sums[pmap[i][0]] = 1;
        } else {
            sums[pmap[i][0]]++;
        }
    }
    for (var p in sums) {
        var pl = game.getPlayerByColor(p);
        if (pl) {
            pl.cellsCount = sums[p];
        }
    }
    game.updatePlayersList();
}
game.onTurn = function (turn) {
    $('div#player' + game.turn).css('border-width', '1px');
    $('div#divTimer' + game.turn).css('visibility', 'hidden');
    game.turn = turn[0];
    game.timer = turn[1];
    if (game.timer<0) {
        game.timer = 0;
    }
    $('div#player' + game.turn).css('border-width', '2px');
    document.getElementById('divTimer' + game.turn).style.width = Math.floor(game.timer/game.TIME_ON_TURN*100)+'%';
    if (! game.replay) {
        $('div#divTimer' + game.turn).css('visibility', 'visible');
    }
    if (game.isYourTurn()) {
        // your turn
    } else {
    }
    
    if (game.isYourTurn()) {
        game.showHint(game.lang('hint_your_turn', game.getColorName(game.turn)));
    } else {
        game.showHint(game.lang('hint_turn', game.fUpper(game.getColorName(game.turn))));
    }
}

game.onStartTutorial = function () {
    game.isTutorial = true;
    document.getElementById('chat_cl').disabled = true;
    document.getElementById('chat_cl').value = game.lang('tut_block_chat');
}

game.onEndTutorial = function () {
    game.isTutorial = false;
    document.getElementById('chat_cl').disabled = false;
    document.getElementById('chat_cl').value = '';
}

game.turnNumber = 0;
game.onTurnNumber = function (turn) {
    game.sysBoard(game.lang('board_turn') + ' ' + turn + '.');
    game.turnNumber = turn;
}
game.onBonusDepot = function (params) {
    var key = params[0];
    var num = params[1];
    game.players[key].depot = num;
    game.updatePlayersList();
}
game.onAttack = function (resp) {
    var fRoll = resp[0];
    var tRoll = resp[1];
    var fCell = resp[2];
    var tCell = resp[3];
    var fPlayerColor = resp[4];
    var tPlayerColor = resp[5];
    if (fCell['color'] == tCell['color']) {
        // attacker won
        var cnt = game.getPlayerByColor(fPlayerColor).cellsCount++;
        cnt = game.getPlayerByColor(tPlayerColor).cellsCount--;
        setTimeout(game.updatePlayersList, 600);
    }
    var tmp = '['
        + '<font class="color' + fPlayerColor + '">' + fRoll.join(',') + '</font>'
        + '] ' + game.lang('board_against') + ' ['
        + '<font class="color' + tPlayerColor + '">' + tRoll.join(',') + '</font>'
        + ']';
    game.sysBoard(tmp);
    game.timer = game.TIME_ON_TURN;
}
game.onDeath = function (resp) {
    var user = resp[0];
    var place = resp[1];
    var score = resp[2];
    var mplace = lang.places[place-1];
    
    if (score > 0) {
        score = '+' + score;
    }
    var txtScore = '';
    if (score) {
        txtScore = ' (' + score + ')';
    }
    game.chat.displayMsg(game.lang('msg_lost', escapeHTML(game.getNickByPlArr(user)), mplace) + txtScore + '.');
    game.players[user.key].rm();
    game.updatePlayersList();
    setTimeout(game.updateTop, 3*1000);
}
game.onWon = function (resp) {
    var user = resp[0];
    var place = resp[1];
    var score = resp[2];
    if (score > 0) {
        score = '+' + score;
    }
    var txtScore = '';
    if (score) {
        txtScore = ' (' + score + ')';
    }
    game.chat.displayMsg(game.lang('msg_won', escapeHTML(game.getNickByPlArr(user))) + txtScore + '.');
    game.players[user.key].rm()
    game.started = false;
    game.players = {};
    game.color2player = {};
    game.updatePlayersList();
}

game.updatePlayersList = function () {
    for (var i=0; i<game.map.max_players; i++) {
        if (game.color2player[i] == undefined) {
            if (game.started) {
                $('div#player' + i).html('<i>' + game.lang('pl_lost') + '</i>');
            } else if (game.areYouInGame()) {
                $('div#player' + i).html('<i>' + game.lang('pl_wait') + '</i>');
            } else if (game.youAre['score'] < game.map.bid && game.map.bid > 49) {
                document.getElementById('player' + i).innerHTML = '<i>' + game.lang('pl_low_score') + '</i>';
            } else if (game.youAre['score'] > game.map.max_score && game.map.max_score > 0) {
                document.getElementById('player' + i).innerHTML = '<i>' + game.lang('pl_high_score') + '</i>';
            } else {
                if (!game.replay) {
                    document.getElementById('player' + i).innerHTML = '<input type="button" class="player'
                        + '" onClick="game.getFlash().sit('
                        + i + ');" value="' + game.lang('play_here') + '"/>';
                }
            }
        } else {
            var p = game.color2player[i];
            var loc = '';
            if (p.country) {
                loc = lang.country[p.country];
                if (p.location) {
                    loc = p.location + ' (' + loc + ')';
                }
            }
            $('div#player' + i).html(
                '<table border="0" width="100%">'
                + '<tr><td style="vertical-align:top;" rowspan="2" width="33">'
                + '<div style="position: relative;">'
                + (p.link ? ('<a href="' + p.link + '" onClick="return game.openLink(\'' + p.link + '\');">') : '')
                + (p.away ? '<img border="0" src="/images/empty.gif" style="left:0;width:36px;height:36px;position:absolute;z-index:100;background: url(/images/away-roll-male.png);"/>':'')
                + (p.banChat ? '<img border="0" src="/images/empty.gif" alt="' + game.lang('pl_ban_chat') + '" title="' + game.lang('pl_ban_chat') + '" style="left:30px;top:-2px;width:12px;height:12px;position:absolute;z-index:100;background: url(/images/ban_icon.png);"/>' : '')
                + '<div style="clip:rect(0px, 36px, 36px, 0px);position:absolute;left:0;">'
                + '<img border="0" src="' + p.photo + '" width="36"/>'
                + '</a>'
                + '</div>'
                + '</div>'
                + '</td>'
                + '<td align="right"><div class="pname">' + escapeHTML(game.getNickByPlArr(p)) + '</div></tr></td>'
                + '<tr><td align="right"><nobr>'
                + (p.country ? '<img border="0" alt="' + loc + '" title="' + loc + '" style="width:16px;height:11px;z-index:100;position:relative;" src="/images/flags_s/' + p.country + '.png"/>&nbsp;': '')
                + '<img src="/images/chess.png" alt="' + game.lang('pl_score') + '" title="' + game.lang('pl_score') + '"/> ' + p.score + ''
                + ((game.started) ? ('&nbsp;<img src="/images/property.png" alt="' + game.lang('pl_lands') + '" title="' + game.lang('pl_lands') + '"/> <font id="lands' + p.id + '">' + p.cellsCount + '</font> ') : '')
                + ((p.depot>0) ? ('&nbsp;<img src="/images/dice_small.png" alt="' + game.lang('pl_depot') + '" title="' + game.lang('pl_depot') + '"/> ' + p.depot):'')
                + '</nobr></td></tr>'
                + '</table>'
            );
        }
    }
}

game.updateTimer = function () {
    if (game.started && game.turn!=undefined) {
        if (game.timer == 1 && game.isTutorial) {
            game.timer = game.TIME_ON_TURN;
        }
        if (game.timer < 1) {
            game.timer = 1.5;
        }
        if (game.timer > 1) {
            game.timer -= 0.5;
            var px = 100 * game.timer / game.TIME_ON_TURN;
            if (document.getElementById('divTimer' + game.turn) != undefined) {
                document.getElementById('divTimer' + game.turn).style.width = px + '%';
                if (game.timer == 2 && game.isYourTurn()) {
                    game.getFlash().shakeBtnEndTurn();
                }
                if (game.timer > 3 && game.timer <= 6) {
                    document.getElementById('divTimer' + game.turn).style.backgroundColor = 'orange';
                } else if (game.timer <= 3) {
                    document.getElementById('divTimer' + game.turn).style.backgroundColor = 'red';
                } else {
                    document.getElementById('divTimer' + game.turn).style.backgroundColor = 'green';
                }
            }
        }
    }
}

game.getPlayerByColor = function (color) {
    for (var key in game.players) {
        if (game.players[key].color == color) {
            return game.players[key];
        }
    }
}

game.getPlayerByKey = function (key) {
    for (var key in game.players) {
        if (game.players[key].key == key) {
            return game.players[key];
        }
    }
}

game.CPlayer = function () {
}
game.CPlayer.prototype.rm = function () {
    delete game.players[this.key];
    if (this.color != null) {
        delete game.color2player[this.color];
    }
}

function escapeHTML(text) {
	return $('<div></div>').text(text).html();
}

$(document).ready(function () {
    if (!game.replay) {
        setInterval('game.nextHint()', 1000);
        setInterval('game.updateTimer()', 500);
        setInterval('game.updateTop()', 1000*60 *5);
        game.updateTop();
        if (game.userlib.reloadFriends != undefined) {
            game.userlib.reloadFriends();
        }
    }
});

game.getNickByPar = function (nick, tp) {
    if (tp==1) {
        return game.lang('guest') + ' ' + lang.romanize(nick);
    } else {
        return lang.romanize(nick);
    }
}

game.getNickByPlArr = function (pl, tp) {
    if (pl['t'] == 'guest' || pl['type'] == 'guest') {
        return game.lang('guest') + ' ' + pl['name'];
    }
    return lang.romanize(pl['name']);
}

game.lang = function (key, var1, var2, var3, var4) {
    var s = lang.messages[key];
    if (s == undefined) {
        console.log('error: language key ' + key + ' does not exist');
        return '';
    }
    if (var1) {
        s = s.replace('%s1%', var1);
        if (var2) {
            s = s.replace('%s2%', var2);
            if (var3) {
                s = s.replace('%s3%', var3);
                if (var4) {
                    s = s.replace('%s4%', var4);
                }
            }
        }
    }
    return s;
}

