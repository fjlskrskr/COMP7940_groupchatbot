from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext,CallbackQueryHandler

import configparser
import logging
import redis

global redis1

def main():
    # Load your token and create an Updater for your Bot
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    global redis1
    redis1 = redis.Redis(host=(config['REDIS']['HOST']), password=(config['REDIS']['PASSWORD']), port=(config['REDIS']['REDISPORT']),decode_responses=True)

    # You can set this logging module, so you will know when and why things do not work as expected
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    # register a dispatcher to handle message: here we register an echo dispatcher
    global reviewer
    reviewer = {}
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("review", review))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("hello", hello_command))
    dispatcher.add_handler(CallbackQueryHandler(callback_handler))
    # To start the bot:
    updater.start_polling()
    updater.idle()
    
def callback_handler(update: Update, context: CallbackContext):
    global reviewer
    query = update.callback_query
    qlist = query.data.split(',',1)
    if qlist[0] in reviewer.keys():
        query.edit_message_text('you should finish your review first')
    else:
        reviewer[qlist[0]] = qlist[1]
        query.answer('loading')
        query.edit_message_text(text='Feel free to post your review!')


def echo(update, context):
    global reviewer
    userid = str(update['message']['chat']['id'])
    if userid in reviewer.keys():
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
        # redis1.hdel('review','')
        print(redis1.hget('review_count',topicname))
        update.message.reply_text( msgsender + ' have said ' + msgtext +  ' at ' + msgid)
        del reviewer[userid]
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text= reviewer)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Helping you helping you.')

def hello_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    # logging.info(context.args[0])
    msg = context.args[0]
    update.message.reply_text('Good day, ' + msg +  '!')

def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try: 
        global redis1
        logging.info(context.args[0])
        msg = context.args[0]   # /add keyword <-- this should store the keyword
        redis1.incr(msg)
        update.message.reply_text('You have said ' + msg +  ' for ' + redis1.get(msg).decode('UTF-8') + ' times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')

def top_n_scores(n, score_dict):
    ''' returns the n most popular from a dict'''
    #make list of tuple from scores dict
    lot = [(k,v) for k, v in score_dict.items()] 
    nl = []
    while len(lot)> 0:
        # maxone = max(lot, key=lambda x: x[1])
        nl.append(max(lot, key=lambda x: x[1]))
        lot.remove(nl[-1])
    return nl[0:n]

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

def review(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /review is issued."""
    try: 
        global redis1
        # logging.info(context.args[0])
        #get input topic
        topicname = context.args[0]
        #get topic data from redis
        topicdata = redis1.hget('review',topicname)
        #get userid
        userid = str(update['message']['chat']['id'])
        #set callback message
        cb_data = userid + ',' + topicname
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
            update.message.reply_text('Here some recent reviews about ' + topicname + ':\n' + recentreview + 'Do you wanna make a review about it?',
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton('write review',callback_data=cb_data)]]))

    except (IndexError, ValueError):
        #if input '/review'
        #get popular topics
        popular = top_n_scores(3,redis1.hgetall('review_count'))
        charlist = ''
        for i in popular:
            char = i[0] + ': ' + i[1] + ' reviews'
            charlist += char + '\n'
        update.message.reply_text('Here some hit TV topics:\n' + charlist + 'Try viewing some reviews by typing:\n /review <topicname>')



if __name__ == '__main__':
    main()