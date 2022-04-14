from flask import Flask, request
from telegram import Bot,InlineKeyboardButton, InlineKeyboardMarkup, Update,ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Dispatcher,MessageHandler,CommandHandler,ConversationHandler,Filters,CallbackQueryHandler
import random
import os
import logging
import redis

import configparser
# config = configparser.ConfigParser()
# config.read('config.ini')

#chatbot api
global bot
#bot token
global TOKEN
#server url
global URL
#redis database
global redis1
#parameter for /route
global v1    #登山评论的value值
SHARE, CHOOSE, PHOTO, CHECK, SHOW = range(5)
#parameter for /review
global reviewer
global sharedict
reviewer = {}
sharedict = {}
config = configparser.ConfigParser()
config.read('config.ini')

#set redis connnection
redis1 = redis.Redis(host=(config['REDIS']['HOST']), password=(config['REDIS']['PASSWORD']), port=(config['REDIS']['REDISPORT']),decode_responses=True, ssl=True)
# redis1 = redis.Redis(host=(os.environ['HOST']), password=(os.environ['PASSWORD']), port=(os.environ['REDISPORT']),decode_responses=True, ssl=True)
#set server url
URL = config['WEBHOOK']['URL']
# URL = os.environ['URL']
#set chatbot token
TOKEN = config['TELEGRAM']['ACCESS_TOKEN']
# TOKEN = os.environ['ACCESS_TOKEN']
bot = Bot(token=TOKEN)
#set webhook for chatbot
bot.setWebhook('{URL}/{HOOK}'.format(URL=URL, HOOK=TOKEN))
#set update dispatcher
dispatcher = Dispatcher(bot,None)

    
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Main page'

# @app.route('/set_webhook', methods=['GET', 'POST'])
# def set_webhook():
#     #webhook setting
#     s = bot.setWebhook('{URL}/{HOOK}'.format(URL=URL, HOOK=TOKEN))
#     if s:
#         return "webhook setup ok"
#     else:
#         return "webhook setup failed"

@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    # logging.info("Update: " + str(update.callback_query))
    
    # chat_id = update.message.chat.id
    # msg_id = update.message.message_id
    # # Telegram understands UTF-8, so encode text for unicode compatibility
    # text = update.message.text.encode('utf-8').decode()

    # print("got text message :", text)
    # response = get_response(text)
    # bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)
    
    # command_handler(update)

    return 'ok'

# def command_handler(update:Update):
#     callback = update.callback_query
#     if callback != None:
#         callback_handler(update)
#         return
#     text = update.message.text
#     text = text.split(' ',1)[0]
#     if text == None:
#         logging.info('Warning: message.text == None')
#         return
#     elif '/review' == text:
#         review(update)
#     else:
#         echo(update)
#     return

#review part built by FJL
def callback_handler(update: Update, context):
    #handle callback data from review
    global reviewer
    global sharedict
    query = update.callback_query
    try:
        qlist = eval(query.data)
        if qlist[0] == 'review':
            #user write review
            if qlist[1] in reviewer:
                #if user have not finish previous review
                query.edit_message_text('you should finish your review first.')
            else:
                #add user id into reviewer dict
                #qlist[1]=userid,qlist[2]=topicname
                reviewer[qlist[1]] = qlist[2]
                query.answer('loading')
                query.edit_message_text(text='Feel free to post your review!')
        elif qlist[0] == 'share':
            #share review to others
            #qlist[1]=username,qlist[2]=topicname
            query.edit_message_text(text='OK, I will tell others about your review!' + qlist[1] + qlist[2])
            #boardcast to other users
        elif qlist[0] == 'shareto':
            if qlist[1] in sharedict:
                #stop receive from others
                del sharedict[qlist[1]]
                query.edit_message_text(text='You have stopped receiving reviews from others.')
            else:
                #start receive from others
                sharedict[qlist[1]] = ''
                query.edit_message_text(text='You have started receiving reviews from others.')
    except:
        query.edit_message_text(text='Error')

def echo(update: Update, context):
    #global for /review
    global reviewer
    global sharedict
    # logging.info("Update: " + str(update))
    # logging.info("context: " + str(context))

    #get user id
    userid = str(update['message']['chat']['id'])
    #if user is in the reviewer(/review)
    if userid in reviewer:
        #get the name and redis data of topic
        topicname = reviewer[userid]
        topicdata = redis1.hget('review',topicname)
        try:
            topicdict = eval(topicdata)
            count = int(redis1.hget('review_count',topicname))
        except (TypeError,SyntaxError):
            topicdict = {}
            count = 0
        #get message id
        msgid = str(update['message']['message_id'])
        #get username
        if update['message']['chat']['last_name'] is None:
            msgsender = update['message']['chat']['first_name']
        else :
            msgsender = update['message']['chat']['first_name'] + ' ' + update['message']['chat']['last_name']
        #get message context
        msgtext = update['message']['text']
        #topicname:{'msgid':{'text':'...','sender':'...'}}
        topicdict[msgid] = {'text':msgtext,'sender':msgsender}
        #save changes on this topic(dict to str)
        dict_str = str(topicdict)
        #upload changes to redis
        redis1.hset('review',topicname,dict_str)
        #redis1[review][topicname][msgid] = msgdict
        count += 1
        redis1.hset('review_count',topicname,count)
        del reviewer[userid]
        # cb_data = str(['share',msgsender,topicname])
        update.message.reply_text('You have posted your review on '+topicname+' !')
        #share new review to other who want to listen
        for i in sharedict:
            if i != userid:
                bot.send_message(chat_id=i, text= msgsender +
                ' just posted a review on '+topicname+':\n'+msgtext)

def top_n_scores(n, score_dict):
    ''' returns the n most popular from a dict'''
    #make list of tuple from scores dict
    lot = [(k,v) for k, v in score_dict.items()] 
    nl = []
    while len(lot)> 0:
        # maxone = max(lot, key=lambda x: x[1])
        nl.append(max(lot, key=lambda x: x[1]))
        lot.remove(nl[-1])
    sortednl = nl[0:n]
    sortednl.reverse()
    return sortednl

def get_recent_reviews(n,reviewdict:dict):
    ''' returns the n most recent reviews from a dict'''
    reviewlist = list(reviewdict.items())
    recentlist = reviewlist[-n:]
    recentlist = list(reversed(recentlist))
    recentreviews = ''
    for i in recentlist:
        review = i[1]['sender'] + ': ' + i[1]['text'] + '\n'
        recentreviews += review
    return recentreviews

def review(update: Update, context) -> None:
    """Send a message when the command /review is issued."""
    #get userid
    userid = str(update['message']['chat']['id'])
    try: 
        global redis1
        # logging.info(context.args[0])
        #get input topic
        text = update.message.text
        text = text.split(' ',1)
        topicname = text[1]
        #get topic data from redis
        topicdata = redis1.hget('review',topicname)
        #set callback message
        cb_data = str(['review',userid,topicname])
        if topicdata is None:
            #if this topic is not exist
            #inlinebutton
            update.message.reply_text(topicname + ' has no reviews yet.\n' + 'Do you wanna make the first one?',
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton('write review',callback_data=cb_data)]]))
        else:
            #get dict of this topic(str to dict),topicdict:{'msgid':{'text':'...','sender':'...'},'msgid1':{...},...}
            topicdict = eval(topicdata)
            #get recent reviews
            recentreview = get_recent_reviews(3,topicdict)
            #inlinebutton
            update.message.reply_text('Here some recent reviews about ' + topicname + ':\n' + recentreview + '\nDo you wanna make a review about it?',
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton('write review',callback_data=cb_data)]]))
    except (IndexError, ValueError):
        #if input '/review'
        #get popular topics
        global sharedict
        # redis1.hdel('review','testtopic4')
        # redis1.hdel('review_count','testtopic4')
        popular = top_n_scores(3,redis1.hgetall('review_count'))
        cb_data = str(['shareto',userid])
        #if user turn on receive option: show ON; otherwise: show OFF
        share_option = 'Receive from others: OFF'
        if userid in sharedict:
            share_option = 'Receive from others: ON'
        if any(popular):
            charlist = ''
            for i in popular:
                char = i[0] + ': ' + i[1] + ' reviews'
                charlist += char + '\n'
            update.message.reply_text('Here some hit TV topics:\n' + charlist + 
                '\nTry viewing some reviews by typing:\n /review <topicname>\n'+
                'I can also share reviews from others with you if you want.',
                reply_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton(share_option,callback_data=cb_data)]]))
        else:
            update.message.reply_text('Try making a reviews by typing:\n /review <topicname>\n'+
                'I can also share reviews from others with you if you want.',
                reply_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton(share_option,callback_data=cb_data)]]))

#review part built by SNN
#输入/start开始流程
def start(update: Update, context) -> int:
    reply_keyboard = [['check', 'add']]
    update.message.reply_text('This is hiking club, you can post your picture and hiking route or '+
                                'check other post ramdonly.\n\n'+
                                '***you can use /cancel to quit this process\n\n'+
                                'use choose function upon keyboard, no need to typewrite',
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE

#选择check跳转到check，或者add跳转到photo，或者跳过到share
def choose(update: Update, context) -> int:
    if update.message.text == 'add':  
        update.message.reply_text(
            'Please upload an picture\n\n'+
            '***if you only want to share hiking route, you can use /skip to skip',
            reply_markup=ReplyKeyboardRemove(),
        )
        redis1.incr('add')  
        return PHOTO
    elif update.message.text == 'check': 
        update.message.reply_text(
            'A random hiking route message will be displayed for you below'
            ,reply_markup=ReplyKeyboardMarkup([['OK']], one_time_keyboard=True),
        )   
        return CHECK
    else:
        return CHOOSE

#从choose来，到share去
def photo(update: Update, context) -> int:
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()

    i = int(redis1.get('add')) #这个用户序号为i的图片
    redis1.hset('climb_photo',f'{user.first_name}{user.last_name}{i}', f'{photo_file.file_id}')

    update.message.reply_text('You can type your keyboard and share your hiking route now')
    return SHARE

#从share来，或者从choose用skip来，结束过程
def share(update: Update, context) -> int:
    user = update.message.from_user
    share_text = update.message.text

    i = int(redis1.get('add'))
    redis1.hset('climb_word',f'{user.first_name}{user.last_name}{i}', share_text)  #该用户序号为i的评论
    update.message.reply_text(
        'Thanks for sharing!'
    )
    return ConversationHandler.END

#skip功能
def skip_photo(update: Update, context) -> int: #跳过上传图片那步
    update.message.reply_text('You chose to share only your text, start your typing!')
    return SHARE

#从choose来，到show去，单纯的线性展示流程，一直点按钮
def check(update: Update, context) -> int:
    user = update.message.from_user
    n = redis1.hlen('climb_word') #获取一共多少条评论
    a1 = random.randint(0,n-1)  #随机数，本来写的三个，觉得因为有图片可能会刷屏就暂时改为一个
    # a2 = a1
    # while a2 == a1:
    #     a2 = random.randint(0,n)
    # a3 = a2
    # while a3 == a2:
    #     a3 = random.randint(0,n)
    w1 = redis1.hkeys('climb_word')[a1] #随机三个key值
    # w3 = redis.hkeys('clim_word')[a3]
    # w2 = redis.hkeys('clim_word')[a2]
    global v1   #这里v1要在下一个def用，所以用了个全局变量
    v1 = redis1.hget('climb_word',w1)  #对应的三个value值
    # v2 = redis.hget('clim_word',w2)
    # v3 = redis.hget('clim_word',w3)
    
    if redis1.hexists('climb_photo',w1) == True:  #检查该分享是否有上传照片
        photovalue = redis1.hget('climb_photo',w1)
        # photovalue = str(photovalue, 'UTF-8')   #redis里的哈希表存的是字节类型，要转一下
        update.message.reply_photo(f'{photovalue}')
        update.message.reply_text(
        f'{v1}',reply_markup=ReplyKeyboardRemove()
        )
        # update.message.reply_text(
        # 'here the share picture.',reply_markup=ReplyKeyboardMarkup([['good']], one_time_keyboard=True)
        # )
    else:
        # update.message.reply_text(
        # 'The author only shared a text.',reply_markup=ReplyKeyboardMarkup([['good']], one_time_keyboard=True)
        # )
        update.message.reply_text('The author only shared a text:')
        update.message.reply_text(
        f'{v1}',reply_markup=ReplyKeyboardRemove()
        )
    return ConversationHandler.END
    # return SHOW

# #从check来，结束过程
# def show(update: Update, context: CallbackContext) -> int:
#     global v1  #check里的全局变量
#     update.message.reply_text(
#         f'{v1}',reply_markup=ReplyKeyboardRemove()
#     )
#     return ConversationHandler.END

#取消功能，输入/cancel可随时退出过程
def cancel(update: Update, context) -> int:
    update.message.reply_text(
        'Bye! ', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

#handle conversation
conv_handler = ConversationHandler(   #能自动回复不需要command指令
        entry_points=[CommandHandler('route', start)],
        states={
            CHOOSE: [MessageHandler(Filters.regex('^(check|add)$'), choose)],
            PHOTO: [MessageHandler(Filters.photo, photo), CommandHandler('skip', skip_photo)],
            SHARE: [MessageHandler(Filters.text & ~Filters.regex('^(good)$'), share), 
                    # CommandHandler('skip', skip_end)
                    ],
            CHECK: [MessageHandler(Filters.regex('^(OK)$'), check)],
            # CHECK: [MessageHandler(Filters.regex('^(good)$'), check)],
            # SHOW: [MessageHandler(Filters.regex('^(good)$'), show)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
dispatcher.add_handler(conv_handler)
#handle eco
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)
#handle /review
dispatcher.add_handler(CommandHandler("review", review))
#handle callback data
dispatcher.add_handler(CallbackQueryHandler(callback_handler))
# dispatcher.add_handler(CommandHandler("help", help_command))
# dispatcher.add_handler(CommandHandler("hello", hello_command))

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    # app.run(threaded=True)