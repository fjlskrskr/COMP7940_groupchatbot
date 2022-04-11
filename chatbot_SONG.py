from lzma import CHECK_CRC32
from sqlalchemy import false, true
from telegram import Update,ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext,ConversationHandler

import configparser
import logging
import redis
import random

import os
from firebase import Firebase

config = {
    'apiKey': '',
    'authDomain':'group-fa3aa.firebaseapp.com',
    'databaseURL': 'https://group-fa3aa-default-rtdb.firebaseio.com/',
    'storageBucket':'group-fa3aa.appspot.com',
    'serviceAccount': 
    {
        "type": "service_account",
        "project_id": "group-fa3aa",
        "private_key_id": "434fa614a4ddb163bd61f8d2c27eaf7892c3d746",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCqs94x5p6TQjqL\nue+FGuG41ZkzzDjTNKPAD/EUW6giUTc7+inL5KkCmzTmg9rAMv9kfWk8P95czixd\nUNs+/Ix/gzAPinw281bd9U/KKzIK4s/7nFfxNWD3SRDlgwkU15IMNLilGTTorTIM\nYMUIQ7sEMBZt3VgCGBgxWSwZ3WjvLhUpsdcI4NTZHipTxpbIMe5LpQ9uXHv28KP8\nf9D3aJf2uuZSuWQCQq5hWxl5NoDEcI3fj74LfF2dWWZ6AeH4VPbbW4EnXdsHJYS4\n7OCXGRMQMElafrVOFXX7BwD323mR6aJuaK2kjMFlIBgXpl6QjjBEuprNYflcqJyI\nVeUd1XhxAgMBAAECggEAD61zU7vthnLHs7uA7wWYA4TCjEpOUb985o/QQWFloLk6\nzGxeWFaI2y9r/VvQxGQqpo0KFDl9b6KT2oIpkLBbKv7edB7w548TxFDaYiPzdaJ9\nHYuvW/zeCfgQ8DNHqz1dMXfKGYemH1SAyzg8AFVQIMNV3AM/KPoThry82ydFkunP\nK6TpzgY/IVUahbH0OtMzoCMauUUXFMxMhvVeISy3WMDCBu6iov/Q9EIoPTQFSgPt\nrWAfg4I9FJrq13jjhpssVfWa/CDDSc3q1vEEyODQqRwnakwQDsvxQyoRW6kjxSk1\nh2yhORhElIlDwIw0nF8gUuuzi1lPe0fqMqIw4sUqwQKBgQDR/vN8ElcIiRzos0/t\ngdymIgtRYLaRVmqsJSeZoxI2NxzIHoiREPcMpuciyvegdfPE5yyb2/BS1QwllYx5\nhyh+Ae5CKnfgu6sZ6n4oPd70k9LTsJ40mReNUYR+xCc2mDUpKAQHPjrQaeNLdQsv\np3YE4PBQK3yQ+rayHKpgWs+W+QKBgQDQGUJl5XsTUPkjkLTYn0qsGSb0WcnMbyCk\noz9Ux/IngJSva9Y/zCVP+os//Y6EhWMQ9seOZxq2PEldM7/skWIbfGlrqGXlbhcp\np0Q+B+xDPJMynS6ecV2wN7kDK6T5bME/G1gTVfeIO8PeYQYPMxx6aYfr/yHlOzlZ\nXPrcduNzOQKBgBZk9vhbSFbLsH6MaNCuUaaR6N0T0ERtj9Ct4aw7vLx1YidhQjUe\nNwptXibSuFevXIC6GoLAkL90ouf7K9Dl/gZ6FDuQJdqciOGppSyLdJRmk0wqAKUh\nUmaqs9OE/Z2P29N4xf0zwLfrIucwIzJAzJA2oMob6RvY8NTLw8ukw5CZAoGAPbig\nNvS/clU7786FtRJZ5X14TlUrQ1VaizpYGF9NdWXvs6/6VeXI01XuY0ZjNO8TGP74\n5UWzaIWtBNXKgPIF9T0LT4Ec59WlTRdtaDCVZMPcrNBt+VSKgy+j0krpnYkiMAN+\nNg3zYxbG23hPgcaZFb2jMN31QbY1JkorpaQlhhECgYBYL+g3M+CN2ab5N2YkZCLC\neup/GS2vAWMyql5Ayy/twwZoMEsiSvSKq8aKYYaAElooUqdopyRyUl1AVWWPmxE9\nuOINGfHYR/T34pfJYfGUtvkBI63AuogjCEIRZEuAZQAnq3I96JSztoSqu2RzJwDh\ng9l/Mi4rUjfo4KuaqiTz/g==\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk-uyj5o@group-fa3aa.iam.gserviceaccount.com",
        "client_id": "100843644760052256510",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-uyj5o%40group-fa3aa.iam.gserviceaccount.com"
    }
}
myfirebase = Firebase(config)
db = myfirebase.database()
storage = myfirebase.storage()

global redis1
global v1
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
def main():
    # config = configparser.ConfigParser()
    # config.read('config.ini') 
    # updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    # dispatcher = updater.dispatcher
    # global redis1
    # redis1 = redis.Redis(host=(config['REDIS']['HOST']), password=(config['REDIS']['PASSWORD']), port=(config['REDIS']['REDISPORT']))
    #上面这些是用来读取config.ini文件里的密码的，现在把密码都放在heroku了，就变成下面的代码了
    updater = Updater(token=(os.environ['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher

    global redis1
    redis1 = redis.Redis(host=(os.environ['HOST']), password=(os.environ['PASSWORD']), port=(os.environ['REDISPORT']))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE: [MessageHandler(Filters.regex('^(check|add)$'), choose)],
            PHOTO: [MessageHandler(Filters.photo, photo), CommandHandler('skip', skip_photo)],
            SHARE: [MessageHandler(Filters.text & ~Filters.regex('^(good)$'), share), 
                    # CommandHandler('skip', skip_end)
                    ],
            CHECK: [MessageHandler(Filters.regex('^(good)$'), check)],
            SHOW: [MessageHandler(Filters.regex('^(good)$'), show)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

SHARE, CHOOSE, PHOTO, CHECK, SHOW = range(5)

def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['check', 'add']]
    update.message.reply_text('登山，查看分享还是添加分享，或输入/cancel取消',
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE

def choose(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user# {'is_bot': False, 'first_name': '', 'id': , 'language_code': '', 'last_name': ''}
    logger.info("%s: %s", user.first_name, update.message.text)
    
    if update.message.text == 'add':  
        update.message.reply_text(
            '请选择要上传的图片',
            reply_markup=ReplyKeyboardRemove(),
        )
        redis1.incr('add')  
        return PHOTO
    elif update.message.text == 'check': 
        update.message.reply_text(
            '下面随机显示yi条',reply_markup=ReplyKeyboardMarkup([['good']], one_time_keyboard=True),
            # reply_markup=ReplyKeyboardRemove(),
        )   
        return CHECK
    else:
        return CHOOSE
'''
    update: 
        {
            'message': 
                {
                    'delete_chat_photo': False, 
                    'photo': [], 
                    'text': 'add',        <-----------------------------
                    'new_chat_photo': [], 
                    'chat': 
                        {
                            'last_name': '资本家', 
                            'type': 'private', 
                            'id': 1993031034, 
                            'first_name': '九条尾巴的'
                        }, 
                    'supergroup_chat_created': False, 
                    'caption_entities': [], 
                    'entities': [], 
                    'group_chat_created': False, 
                    'new_chat_members': [], 
                    'date': 1649588723, 
                    'message_id': 218, 
                    'channel_chat_created': False, 
                    'from': 
                        {
                            'language_code': 'zh-hans', 
                            'is_bot': False, 
                            'id': 1993031034, 
                            'first_name': '九条尾巴的', 
                            'last_name': '资本家'
                        }
                    }, 
            'update_id': 252582031
        }
    '''

def photo(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()

    i = int(redis1.get('add')) #这个用户第i张图片
    # photo_file.download(f'user_photo{i}.jpg')
    # storage.child(f'{user.first_name} {user.last_name}/user_photo{i}.jpg').put(f'user_photo{i}.jpg') #传到firebase

    # storage.downloadURLWithCompletion   #这里少一个获取url的函数，暂时还没查到
    # redis1.hset('climb_photo',f'{user.first_name}{user.last_name}{i}', f'user_photo{i}.jpg')  #在redis里存个序号
    redis1.hset('climb_photo',f'{user.first_name}{user.last_name}{i}', f'{photo_file.file_id}')
    # os.remove(f'user_photo{i}.jpg')  #把本地文件删了

    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
    update.message.reply_text('请输入分享内容')
    return SHARE
'''
update: 
    {
        'message': 
            {
                'photo': [
                    {
                        'height': 79, 
                        'file_unique_id': 'AQADia8xG4RdmFZ4', 
                        'file_id': 'AgACAgUAAxkBAAPmYlK94F_BSU3DIRKR-msWjjHCLVAAAomvMRuEXZhWFN7CUhifU78BAAMCAANzAAMjBA', 
                        'width': 90, 
                        'file_size': 1332
                    }, 
                    {
                        'height': 280, 
                        'file_unique_id': 'AQADia8xG4RdmFZy', 
                        'file_id': 'AgACAgUAAxkBAAPmYlK94F_BSU3DIRKR-msWjjHCLVAAAomvMRuEXZhWFN7CUhifU78BAAMCAANtAAMjBA', 
                        'width': 320, 
                        'file_size': 21232
                    }, 
                    {
                        'height': 668, 
                        'file_unique_id': 'AQADia8xG4RdmFZ9', 
                        'file_id': 'AgACAgUAAxkBAAPmYlK94F_BSU3DIRKR-msWjjHCLVAAAomvMRuEXZhWFN7CUhifU78BAAMCAAN4AAMjBA', 
                        'width': 764, 
                        'file_size': 99986
                    }     ], 
                'chat': {'last_name': '资本家', 'first_name': '九条尾巴的', 'id': 1993031034, 'type': 'private'}, 
                'group_chat_created': False, 
                'new_chat_members': [], 
                'new_chat_photo': [], 
                'delete_chat_photo': False, 
                'caption_entities': [], 
                'message_id': 230, 
                'supergroup_chat_created': False, 
                'entities': [], 
                'date': 1649589728, 
                'channel_chat_created': False, 
                'from': {'last_name': '资本家', 'is_bot': False, 'first_name': '九条尾巴的', 'id': 1993031034, 'language_code': 'zh-hans'}
            }, 
        'update_id': 252582037
    }
'''
'''
photo_file: 
    {
        'file_size': 16590, 
        'file_unique_id': 'AQADpq8xG4RdmFZ8', 
        'file_id': 'AgACAgUAAxkBAAPsYlLDqjh3RTbj7bEnlfro-yYpnz0AAqavMRuEXZhW4bdknNdKB8oBAAMCAAN3AAMjBA', 
        'file_path': 'https://api.telegram.org/file/bot5157169918:AAGDsFgGxvY3PJNebbeKJy5sh1YBYKj3Cf8/photos/file_2.jpg'
    }
'''

def share(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    share_text = update.message.text
    logger.info(
        " %s: %f", user.first_name, share_text
    )

    i = int(redis1.get('add'))
    redis1.hset('climb_word',f'{user.first_name}{user.last_name}{i}', share_text)  #该用户序号为i的评论
    update.message.reply_text(
        '感谢分享'
    )
    return ConversationHandler.END

def skip_photo(update: Update, context: CallbackContext) -> int: #跳过上传图片那步
    user = update.message.from_user
    logger.info("User %s did not share a photo.", user.first_name)
    update.message.reply_text(
        'ok.'
    )
    return SHARE

def check(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    # print(redis1.keys()) # 查询所有的Key
    # print(redis1.dbsize())   # 当前redis包含多少条数据
    # print(redis1.hgetall('climb_word'))
    n = redis1.hlen('climb_word') #获取一共多少条评论
    a1 = random.randint(0,n-1)
    # a2 = a1
    # while a2 == a1:
    #     a2 = random.randint(0,n)
    # a3 = a2
    # while a3 == a2:
    #     a3 = random.randint(0,n)
    # print(redis1.hkeys('climb_word'))
    w1 = redis1.hkeys('climb_word')[a1] #随机三个key值
    # print(w1)
    # w3 = redis.hkeys('clim_word')[a3]
    # w2 = redis.hkeys('clim_word')[a2]
    global v1
    v1 = redis1.hget('climb_word',w1)  #对应的三个value值
    # print(v1)
    # v2 = redis.hget('clim_word',w2)
    # v3 = redis.hget('clim_word',w3)
    
    if redis1.hexists('climb_photo',w1) == true:
        photovalue = redis1.hget('climb_photo',w1)
        photovalue = str(photovalue, 'UTF-8')
        # print(photovalue)
        # storage.child(f'{w1}/{photovalue}').download('download.jpg')
        update.message.reply_photo(f'{photovalue}')
    else:
        update.message.reply_text(
        'auther did not share picture.',reply_markup=ReplyKeyboardMarkup([['good']], one_time_keyboard=True)
        )
    # redis1.delete()
    return SHOW
    
def show(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s.", user.first_name)

    global v1
    update.message.reply_text(
        f'{v1}',reply_markup=ReplyKeyboardMarkup([['good']], one_time_keyboard=True)
    )
    # os.remove('download.jpg')
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! ', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

if __name__ == '__main__':
    main()








