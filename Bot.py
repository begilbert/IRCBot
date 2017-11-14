#!/Library/Frameworks/Python.framework/Versions/3.4/bin/python3.4
# IRC Bot connecting to Freenode IRC Server
# Logs sent as .txt files to folder "KYMIRCLogs"
import socket, codecs, sys, os, traceback
from datetime import timedelta, datetime as dt
from html.parser import HTMLParser
from random import randrange, choice
from re import sub
from urllib.request import urlopen, HTTPError
startdt = dt.now().date()
logfile = os.path.expanduser('~/Documents/KYMIRCLogs/IRCLogs(%s).txt' % startdt)
backupfile = 'backuplog.txt'
if len(sys.argv) >= 2:
    logfile = sys.argv[1]
    if len(sys.argv) == 3:
        backupfile = sys.argv[2]
print('Welcome to Benjamin\'s Python Freenode IRC Client!')
def welcome():
    IRCLog = open(logfile, 'w')
    IRCLog.write('Welcome to Benjamin\'s Python IRC Logs!\r\n')
    IRCLog.write('Log started on: %s\r\n' % dt.now())
    IRCLog.close()
if not os.path.isfile(logfile):
    welcome()
open(backupfile, 'wb').close()
uni = 'utf-8'
iso = 'ISO-8859-1'
escape = lambda string: codecs.getdecoder('unicode_escape')(string)[0]
ent = lambda code: HTMLParser().unescape(code)
style = lambda string, x: escape('\\x{0}{1}\\x{0}'.format(x, string))
getcode = lambda url: urlopen(url).read().decode(uni)
def find(info, string):
    if info.find(string) != -1:
        return(True)
    else:
        return(False)
def log(data):
    with codecs.open(logfile, 'a', uni) as file:
        file.write(data + '\r\n')
        try:
            print(data)
        except UnicodeEncodeError:
            print(data.encode(uni).decode('ascii', 'replace'))
def remove(string, *r):
    for s in r:
        string = sub(s, '', string)
    return(string)
def statuscheck(user):
    if status[user] == 'operator':
        return('@' + user)
    elif status[user] == 'voice':
        return('+' + user)
    else:
        return(user)
def timestamp():
    time = []
    for t in (dt.now().hour, dt.now().minute, dt.now().second):
        if len(str(t)) == 1:
            time.append('0' + str(t))
        else:
            time.append(str(t))
    return('(%s)' % ':'.join(time))
def verify(url):
    try:
        getcode(url)
    except (UnicodeEncodeError, HTTPError):
        return(False)
    else:
        return(True)
class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._data = []
        self.underline = None
    def handle_data(self, data):
        self._data.append(data)
    def handle_starttag(self, tag, attrs=''):
        if tag == 'img':
            for attr in attrs:
                if attr[0] == 'data-src':
                    self._data.append(attr[1])
        elif tag == 'br' or tag == 'p':
            self._data.append(' ')
        elif tag == 'em' or tag == 'i':
            self._data.append('\\x16')
        elif tag == 'b' or tag == 'strong':
            self._data.append('\\x02')
        for attr in attrs:
            if attr[0] == 'style' and attr[1] == 'text-decoration: underline;':
                self.underline = tag
                self._data.append('\\x1f')
    def handle_endtag(self, tag):
        if tag == self.underline:
            self._data.append('\\x1f')
            self.underline = None
        self.handle_starttag(tag)
    @property
    def data(self):
        return(escape(' '.join(''.join(self._data).split())))
nick = input("Provide a nickname:")
realname = input("Provide a realname:")
print("Enter your Freenode username")
user = input("Press \"Enter\" if you have not yet registered:")
if user:
    password = input('Type your password:')
else:
    user = nick
    password = ''
chan = input("Which channel do you wish to join?:")
server = 'chat.freenode.net'
class fn(socket.socket):
    def send(self, output):
        super().send(bytes(output + '\r\n', uni))
    def msg(self, output, action=False):
        if len(output) > 400:
            output = output[:390] + '. . . (etc)'
        if action:
            self.send('PRIVMSG %s :\x01ACTION %s\x01' % (chan, output))
        else:
            self.send('PRIVMSG %s :%s' % (chan, output))
    def logmsg(self, output, action=False):
        self.msg(output, action)
        if len(output) > 400:
            output = output[:390] + '. . . (etc)'
        if action:
            log('%s * %s %s' % (timestamp(), nick, output))
        else:
            log('%s %s: %s' % (timestamp(), nick, output))
    def quit(self, msg='Later all!', exit=0):
        self.send('QUIT :%s' % msg)
        super().close()
        sys.exit(exit)
irc = fn(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((server, 6667))
irc.send('NICK %s' % nick)
irc.send('USER %s 8 * :%s' % (user, realname))
if password:
    irc.send('PRIVMSG NickServ :identify %s' % password)
irc.send('JOIN %s' % chan)
log('Joining. . .')
ident = False
join = False
topic = False
def client(text):
    global ident, join, topic, status, startdt, logfile
    if startdt < dt.now().date():
        startdt = dt.now().date()
        logfile = os.path.expanduser('~/Documents/KYMIRCLogs/IRCLogs(%s).txt'
                                     % startdt)
        welcome()
    sep = text.split()
    if find(text, '!'):
        usr = text[1:text.index('!')]
    def setmode(mode):
        del status[sep[4]]
        status.update({sep[4] : mode})
        log('%s %s has set mode: %s %s' % (timestamp(), usr, sep[3], sep[4]))
    if text.startswith('PING'):
        irc.send('PONG %s' % sep[1])
    if join:
        if find(text, 'PRIVMSG'):
            if sep[3].startswith(':\x01ACTION'):
                log('%s * %s %s' % (timestamp(), statuscheck(usr),
                                    text[1:][text[1:].index(' :') + 10:]))
            else:
                log('%s %s: %s'
                    % (timestamp(), statuscheck(usr),
                       text[1:][text[1:].index(' :') + 2:]))
        elif find(text, 'PART') or find(text, 'QUIT'):
            if len(text.split()) > 3:
                log('%s %s has left %s (%s)'
                    % (timestamp(), usr, chan,
                       text[1:][text[1:].index(' :') + 2:]))
            else:
                log('%s %s has left %s ()' % (timestamp(), usr, chan))
            del status[usr]
        elif find(text, 'KICK'):
            if sep[3] == nick:
                log('%s %s has been kicked from %s by %s (%s)'
                    % (timestamp(), sep[3], chan, usr,
                       text[1:][text[1:].index(' :') + 2:]))
                irc.send('JOIN %s' % chan)
                print('Rejoining. . .')
                join = False
            else:
                log('%s %s has been kicked from %s by %s (%s)'
                    % (timestamp(), sep[3], chan, usr,
                       text[1:][text[1:].index(' :') + 2:]))
                del status[sep[3]]
        elif find(text, 'JOIN'):
            log('%s %s (addr:[%s]) has joined %s'
                % (timestamp(), usr, sep[0][text.index('!') + 1:], chan))
            status.update({usr : 'user'})
        elif find(text, 'NICK'):
            log('%s %s has changed their nick to %s'
                % (timestamp(), usr, sep[2][1:]))
            status.update({sep[2][1:] : status[usr]})
            del status[usr]
        elif find(text, 'TOPIC'):
            log('%s %s has changed the topic of %s to: %s'
                % (timestamp(), usr, chan, text[1:][text[1:].index(' :') + 2:]))
        elif find(text, 'MODE'):
            if len(text.split()) < 5:
                log('%s %s has set mode: %s %s'
                    % (timestamp(), usr, sep[3], chan))
            elif text.find('+o') != -1:
                setmode('operator')
            elif text.find('-o') != -1 or text.find('-v') != -1:
                setmode('user')
            elif text.find('+v') != -1:
                setmode('voice')
        if find(text, 'http://knowyourmeme.com/comments/'):
            message = text[1:][text[1:].index(' :') + 2:] + ' '
            piece = message[message.index("http://knowyourmeme.com/comments"):]
            link = piece[:piece.index(' ')]
            if not verify(link):
                irc.logmsg('Comment error: 404 page not found')
            else:
                html = getcode(link)
                userparse = html[html.index('comment_body'):]
                section = userparse[userparse.index('<h6>'):
                                    userparse.index('</h6>')]
                usr = remove(ent(section.replace('\n', ' ')), r'\<.*?\>')[:-1]
                content = html[html.index('message'):][9:].replace('\n', ' ')
                comment = ent(content[:content.index(
                    '<div class=\'comment-bottom-bar\'>')])
                parser = LinkParser()
                parser.feed(comment)
                irc.logmsg('%s %s' % (style('Comment by%s:' % usr, '02'),
                                      parser.data))
        if find(text, 'http://knowyourmeme.com/forums') and find(
            text, '#forum_post_'):
            message = text[1:][text[1:].index(' :') + 2:] + ' '
            parse = message[message.index("http://knowyourmeme.com/forums/"):]
            link = parse[:parse.index(' ')]
            post = parse[parse.index('forum_post_'):parse.index(' ')]
            if verify(link):
                html = getcode(link)
                if html.find(post) == -1:
                    irc.logmsg('Post Error: Forum post not found')
                else:
                    parser = LinkParser()
                    body = html[html.index(post):]
                    div = ent(body[body.index(
                        '<div class=\'bodycopy moderate\'>'):])
                    section = div[:div.index('</section>')]
                    estamp = '<div class=\'last_edited\'>'
                    if section.find(estamp) != -1:
                        section = section[:section.index(estamp)]
                    parser.feed(section)
                    irc.logmsg('%s %s' % (style('Forum post: ', '02'),
                                          parser.data))
    elif len(sep) >= 2:
        if sep[1] == '376':
            ident = True
        elif sep[1] == '353' and ident:
            join = True
            status = {}
            if not topic:
                log('You have joined the channel')
                log('%s channel topic: [no set topic]' % chan)
            parsetext = text[text.index('353'):]
            userlist = parsetext[parsetext.index(':') + 1:].split()
            for name in userlist:
                if '@' in name:
                    name = name.replace('@', '')
                    status.update({name : 'operator'})
                elif '+' in name:
                    name = name.replace('+', '')
                    status.update({name : 'voice'})
                else:
                    status.update({name : 'user'})
        elif sep[1] == '332' and ident:
            log('You have joined the channel')
            log('%s channel topic: %s' % (chan, text[text[1:].index(':') + 2:]))
            topic = True
    if find(text, '!stats'):
        irc.logmsg('stats are down http://stats.neonwabbit.com/KYM/')
    if find(text, '!quit'):
        irc.send('WHOIS %s' % usr)
        i = 0
        while i < 5:
            i += 1
            line = irc.recv(2040).decode(uni)
            if ':End of /WHOIS list.' in line:
                if ['Muffinlicious'] in line.split('\r\n'):
                    irc.quit()
                else:
                    break
timer = dt.now() + timedelta(seconds=12)
spam = 0
ball = 0
def runirc(bytestr, func=None):
    decoder = uni
    try:
        node = bytestr.decode(uni)
    except UnicodeDecodeError:
        node = bytestr.decode(iso)
        decoder = iso
    try:
        with codecs.open(backupfile, 'ab',) as bl:
            bl.write(bytestr)
        for msg in node.split('\r\n'):
            client(msg)
            if join and func:
                func(msg)
    except Exception:
        traceback.print_exc()
        sys.stderr.write('Cause: ' + repr(msg))
        irc.quit('Error detected', exit=1)
    return(decoder)
def bot(text):
    global spam, timer, ball
    sep = text.split()
    if find(text, '!'):
        usr = text[1:text.index('!')]
    if find(text, ':!mute') and (status[usr] == 'operator'
                                 or status[usr] == 'voice'):
        try:
            while 1:
                rawdata = irc.recv(2040)
                data = rawdata.decode(runirc(rawdata))
                if find(data, ':!unmute') and (
                    status[data[1:data.index('!')]] == 'operator' or
                    status[data[1:data.index('!')]] == 'voice'):
                    break
        except KeyboardInterrupt:
            irc.quit()
    elif find(text, ':!enable'):
        ball = True
    elif find(text, ':!disable'):
        ball = False
    elif find(text, 'uwu'):
        irc.logmsg('slaps %s with a %s' % (usr, style('big black cock', '02')),
                   True)
        spam += 1
    elif find(text, ':!whois'):
        bleh = text[1:][text[1:].index(' :') + 2:].split()[1]
        irc.send('WHOIS %s' % bleh)
    elif find(text, ':!slap'):
        slap = '\x034r\x037a\x038i\x0311n\x0313b\x0312o\x0310w \
\x039t\x034r\x032o\x032u\x033t\x03'
        if len(sep) > 4:
            if (text[1:]
                [text[1:].index(' :') + 2:].
                split()[0]) != ':!slap' and usr == 'archaicex':
                irc.logmsg('slaps ArchaicEX for failing to ruse\
MuffinBot\'s slap function', True)
            else:
                irc.msg('slaps %s with a %s'
                        % (text[1:][text[1:].index(' :') + 2:].split()[1],
                           slap), True)
                log('%s * %s slaps %s with a rainbow trout'
                    % (timestamp(), statuscheck(nick),
                       text[1:][text[1:].index(' :') + 2:].split()[1]))
        else:
            irc.msg('slaps %s with a %s' % (usr, slap), True)
            log('%s * %s slaps %s with a rainbow trout'
                % (timestamp(), statuscheck(nick), usr))
        spam += 1
    elif find(text, ':!8ball') and ball:
        pro = ['Yes', 'It is decidedly so', 'Without a doubt',
               'You may rely on it', 'As I see it, yes', 'Most likely',
               'Outlook good', 'Signs point to yes']
        neutral = ['Reply hazy; try again', 'Ask again later', 'It is possible',
                   'Maybe', 'Cannot predict now', 'Better not to tell you now']
        con = ['Don\'t count on it', 'Sources say no', 'Outlook not so good',
               'Very doubtful', 'No']
        n = randrange(0, 21)
        if n <= 9:
            result = choice(pro)
            out = style(result, '033')
        elif n <= 17:
            result = choice(con)
            out = style(result, '034')
        else:
            result = choice(neutral)
            out = style(result, '032')
        irc.msg(style(out, '02'))
        log('%s %s: %s' % (timestamp(), statuscheck(nick), result))
        spam += 1
    elif find(text, ':!meme'):
        irc.logmsg('ayy lmao')
        spam += 1
    elif find(text, ':!yiff'):
        irc.logmsg('yiff yiff')
        spam += 2
    elif find(text, ':!profile'):
        irc.logmsg('http://knowyourmeme.com/users/%s'
                   % '-'.join(text[1:][text[1:].index(' :') + 2:].split()[1:]))
    elif find(text, ':!urban'):
        try:
            queue = '+'.join(text[1:][text[1:].index(' :') + 2:].split()[1:])
        except IndexError:
            pass
        else:
            if not verify('http://www.urbandictionary.com/define.php?term=%s'
                          % queue):
                irc.logmsg('Page for "%s" does not exist' % queue)
            else:
                urban = getcode('http://www.urbandictionary.com/define.php?term=%s'
                                % queue)
                parse = urban[urban.index('meaning'):]
                content = parse[:parse.index('</div>')].replace('\r', ' ')\
                          .split('\n')
                definition = remove(ent(content[1]), r'\<.*?\>')
                if not definition:
                    irc.logmsg('Urban error: 404 page not found')
                else:
                    irc.logmsg(' '.join(definition.split()))
    elif find(text, ':!kymt'):
        casename = {'randomman' : 'RandomMan', 'blue screen of death' :
                     'Blue Screen of Death', 'neonwabbit' : 'NeonWabbit',
                     'slime cap' : 'Slime \'Cap', 'triplea9000' : 'TripleA9000',
                     'sir-soundwave' : 'Sir-Soundwave', 'holycrapitsbob' :
                     'HolyCrapItsBob', 'twenty-one' : 'Twenty-One', 'mscratch' :
                     'MScratch', 'jesus of new york (jony)' :
                     'Jesus of New York (JONY)', 'mr. j' : 'Mr. J',
                    'lezhuarez' : 'LezHuarez'}
        title = text[1:][text[1:].index(' :') + 8:]
        raw = list(title.lower())
        for i in range(len(raw) - 1):
            if raw[i] == ' ':
                raw[i + 1] = raw[i + 1].upper()
        article = ''.join(raw)
        if article.lower() in list(casename):
            article = casename[article.lower()]
        urlname = article.replace(' ', '_')
        if not verify('http://kymt.wikia.com/wiki/%s' % urlname):
            irc.logmsg('Page for "%s" does not exist' % article)
        else:
            html = getcode('http://kymt.wikia.com/wiki/%s' % urlname)
            content = remove(html[html.index('<span class="mw-headline"'):],
                             r'\<figure.*?\</figure>', r'\<.*?\>', '\t')
            kymt = content[content.index('Edit'):][5:].lstrip('\n')
            section = ent(kymt[:kymt.index('\n')])
            if section.startswith('r":'):
                section = 'There is no "About" section for %s' % article
            irc.logmsg(section)
        spam += 1
    elif find(text, ':!commands'):
        irc.logmsg('!slap, !urban, !kymt | OP and voice: !mute, !unmute | OP:\
 !quit')
        irc.logmsg('I can also display KYM comments and forum posts')
    if dt.now() >= timer and spam < 4:
        timer = dt.now() + timedelta(seconds=12)
        spam = 0
    elif spam >= 3:
        wait = dt.now() + timedelta(seconds=100)
        spam = 0
        irc.logmsg('Spam detected! Shutting down for 100 sec.')
        while dt.now() < wait:
            runirc(irc.recv(2040))
try:
    while 1:
        runirc(irc.recv(2040), bot)
except KeyboardInterrupt:
    irc.quit()

