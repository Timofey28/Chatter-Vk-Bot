from data import token, my_token, dima_token, my_id, dima_id, V, bot_id
from data import t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_api
import requests
import json
import vk_api.keyboard as kb

from background import keep_alive
keep_alive()

session = vk_api.VkApi(token=token)
vk = session.get_api()
longpoll = VkLongPoll(session)

tokens = [t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11]
ids = [requests.get(f"https://api.vk.com/method/users.get?access_token={t}&v={V}").json()["response"][0]["id"] for t in tokens]
token_full_names = list(
    map(lambda x: f'{x["first_name"]} {x["last_name"]}', vk.users.get(user_ids=','.join(list(map(str, ids))))))
token_names = list(map(lambda x: f'{x["first_name"]}', vk.users.get(user_ids=','.join(list(map(str, ids))))))
info = []  # элемент: [[id аккаунта, имя аккаунта, [id, unread_count]], [.., .., ..], [.., .., ..]]
people = {}
account_index = -1
incoming_id = 0
unread_chats = {}
unread_messages_amount = 0
A1, A2 = False, False

kStart = kb.VkKeyboard(one_time=True)
kStart.add_button("Инфо", "primary")
kStart.add_line()
kStart.add_button("Все аккаунты", "primary")
kStart.add_line()
kStart.add_button("Ссылки на аккаунты", "primary")
kStart = kStart.get_keyboard()

kAfterSendingFwrd = kb.VkKeyboard(one_time=True)
kAfterSendingFwrd.add_button("Отметить прочитанным", "primary")
kAfterSendingFwrd.add_line()
kAfterSendingFwrd.add_button("Назад", "primary")
kAfterSendingFwrd.add_button("Ответить", "primary")
kAfterSendingFwrd.add_line()
kAfterSendingFwrd.add_button("Вернуться в главное меню", "primary")
kAfterSendingFwrd = kAfterSendingFwrd.get_keyboard()

print("Бот запущен")


def main():
    global info, people, account_index, incoming_id, unread_chats, unread_messages_amount, A1, A2
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            msg = event.text.strip()
            if event.user_id != my_id:
                if event.user_id in ids:
                    vk.messages.markAsRead(user_id=event.user_id)
                    continue
                vk.messages.send(user_id=event.user_id, message="wrong chat, buddy", random_id=0)
                continue
            if A1:
                if msg == "В главное меню":
                    A1 = False
                    vk.messages.send(user_id=my_id, message='Главное меню', keyboard=kStart, random_id=0)
                elif msg in people:
                    A1 = False
                    A2 = True
                    account_index = people["account_index"]
                    incoming_id = people[msg][0]
                    unread_messages_amount = people[msg][1]
                    sendFwrds()
                continue

            if A2:
                if msg == "Отметить прочитанным":
                    requests.get(
                        f"https://api.vk.com/method/messages.markAsRead?peer_id={incoming_id}&access_token={tokens[account_index]}&v={V}")
                    A2 = False
                    for acc in info:
                        if acc[0] == account_index:
                            unread_chats = acc[2]
                            break
                    del unread_chats[incoming_id]
                    if unread_chats:
                        A1 = True
                        vk.messages.send(user_id=my_id, message='Отметил 😉', random_id=0)
                        sendUnreadChats()
                    else:
                        info = list(filter(lambda x: x[2], info))
                        vk.messages.send(user_id=my_id, message='Отметил 😉', keyboard=kStart, random_id=0)
                        kInfoList = getInfo(True)
                        for kil in kInfoList:
                            vk.messages.send(user_id=my_id, message='<3', keyboard=kil, random_id=0)
                        if not kInfoList:
                            vk.messages.send(user_id=my_id, message='Непрочитанных сообщений больше нет 😎', keyboard=kStart, random_id=0)
                        else:
                            vk.messages.send(user_id=my_id, message='Главное меню', keyboard=kStart, random_id=0)
                elif msg == "Назад":
                    A2 = False
                    A1 = True
                    sendUnreadChats()
                elif msg == "Ответить":
                    A2 = False
                    someError = False
                    person = requests.get(f"https://api.vk.com/method/users.get?user_ids={incoming_id}&name_case=dat&access_token={my_token}&v={V}").json()["response"][0]
                    vk.messages.send(user_id=my_id, message=f"Сообщение {person['first_name']} {person['last_name']}:", random_id=0)
                    for event2 in longpoll.listen():
                        if event2.type == VkEventType.MESSAGE_NEW and event2.to_me:
                            if event2.user_id != my_id:
                                vk.messages.send(user_id=event2.user_id, message="wrong chat, buddy", random_id=0)
                                continue
                            msg = event2.text.strip()
                            if msg.lower() == "не надо":
                                sendFwrds()
                                A2 = True
                                someError = True
                                break
                            atts = event2.attachments.copy()
                            counter = 0
                            attachments = ''
                            for a in atts:
                                if counter % 2 == 0 and counter != 0:
                                    attachments += ','
                                attachments += atts[a]
                                counter += 1
                            url = f"https://api.vk.com/method/messages.send?user_id={incoming_id}&message={msg}&attachment={attachments}&random_id=0&access_token={tokens[account_index]}&v={V}"
                            try:
                                requests.get(url)
                            except:
                                vk.messages.send(user_id=my_id, message="Не удалось отправить", keyboard=kStart,
                                                 random_id=0)
                                someError = True
                            break
                    if someError:
                        continue
                    for acc in info:
                        if acc[0] == account_index:
                            unread_chats = acc[2]
                            break
                    del unread_chats[incoming_id]
                    if unread_chats:
                        A1 = True
                        vk.messages.send(user_id=my_id, message='Отправил 😉', random_id=0)
                        sendUnreadChats()
                    else:
                        info = list(filter(lambda x: x[2], info))
                        vk.messages.send(user_id=my_id, message='Отправил 😉', keyboard=kStart, random_id=0)
                elif msg == "Вернуться в главное меню":
                    A2 = False
                    vk.messages.send(user_id=my_id, message='Главное меню', keyboard=kStart, random_id=0)

                continue

            if msg == "Инфо" or msg == "Все аккаунты":
                kInfoList = getInfo(True if msg == "Инфо" else False)
                for kil in kInfoList:
                    vk.messages.send(user_id=my_id, message='<3', keyboard=kil, random_id=0)
                if not kInfoList:
                    vk.messages.send(user_id=my_id, message='Непрочитанных сообщений нет 😎', keyboard=kStart, random_id=0)
                else:
                    vk.messages.send(user_id=my_id, message='Главное меню', keyboard=kStart, random_id=0)

            elif msg == "Ссылки на аккаунты":
                getActiveAccounts()

            elif msg in list(map(lambda x: x[1], info)):
                account_index = -1
                unread_chats = ''
                for acc in info:
                    if acc[1] == msg:
                        account_index = acc[0]
                        unread_chats = acc[2]
                        A1 = True
                        break
                sendUnreadChats()

            else:
                vk.messages.send(user_id=my_id, message='Главное меню', keyboard=kStart, random_id=0)


def sendFwrds():
    global A1, A2
    url = f'https://api.vk.com/method/messages.getHistory?peer_id={incoming_id}&count={unread_messages_amount + 10}&access_token={tokens[account_index]}&v={V}'
    history = requests.get(url).json()["response"]["items"]
    fwrd = [msg["id"] for msg in history[:unread_messages_amount] if "action" not in msg]
    if not fwrd:
        vk.messages.send(user_id=my_id,
                         message="В данном чате были пропущенные события, среди которых не было сообщений от пользователей, поэтому отмечаю чат прочитанным",
                         random_id=0)
        requests.get(f"https://api.vk.com/method/messages.markAsRead?peer_id={incoming_id}&access_token={tokens[account_index]}&v={V}")
        for acc in info:
            if acc[0] == account_index:
                del acc[2][incoming_id]
                if not acc[2]:
                    info.remove(acc)
                break
        A1 = True
        A2 = False
        if unread_chats:
            sendUnreadChats()
        else:
            kInfoList = getInfo(True)
            for kil in kInfoList:
                vk.messages.send(user_id=my_id, message='<3', keyboard=kil, random_id=0)
            if not kInfoList:
                vk.messages.send(user_id=my_id, message='Непрочитанных сообщений больше нет 😎', keyboard=kStart, random_id=0)
            else:
                vk.messages.send(user_id=my_id, message='Главное меню', keyboard=kStart, random_id=0)
        return

    for msg in history[unread_messages_amount:]:
        if "out" in msg and msg["out"] == 0:
            break
        if "action" not in msg:
            fwrd.append(msg["id"])
    url = f"https://api.vk.com/method/messages.send?peer_id=-{bot_id}&message=Без проблем бро, вот наша переписка&forward_messages={','.join(list(map(str, fwrd)))}&random_id=0&access_token={tokens[account_index]}&v={V}"
    requests.get(url)
    history = vk.messages.getHistory(user_id=ids[account_index], count=1)
    vk.messages.send(user_id=my_id, forward_messages=history["items"][0]["id"], keyboard=kAfterSendingFwrd, random_id=0)


def sendUnreadChats():
    global people
    people = {"account_index": account_index}
    account = requests.get(f"https://api.vk.com/method/users.get?user_ids={ids[account_index]}&name_case=gen&access_token={my_token}&v={V}").json()["response"][0]
    gen_name = f"{account['first_name']} {account['last_name']}"
    kUnreadChats = kb.VkKeyboard(inline=True)
    counter = 0
    if len(unread_chats) == 1:
        for um in unread_chats:
            person = getChatName(um)
            people[f"{person} ({unread_chats[um]})"] = [um, unread_chats[um]]
            kUnreadChats.add_button(f"{person} ({unread_chats[um]})", "positive")
            kUnreadChats.add_line()
            kUnreadChats.add_button("В главное меню", "primary")
            msg = "Непрочитанный чат " + gen_name
            vk.messages.send(user_id=my_id, message=msg, keyboard=kUnreadChats.get_keyboard(), random_id=0)
            return
    for um in unread_chats:
        person = getChatName(um)
        if counter % 6 == 0 and counter != 0:
            msg = f"Непрочитанные чаты {gen_name} ({counter - 5}-{counter})"
            vk.messages.send(user_id=my_id, message=msg, keyboard=kUnreadChats.get_keyboard(), random_id=0)
            kUnreadChats = kb.VkKeyboard(inline=True)
        elif counter != 0:
            kUnreadChats.add_line()
        kUnreadChats.add_button(f"{person} ({unread_chats[um]})", "positive")
        people[f"{person} ({unread_chats[um]})"] = [um, unread_chats[um]]
        if counter == len(unread_chats) - 1:
            on = counter + 1 - counter % 6
            to = counter + 1
            msg = "Непрочитанные чаты "
            msg = f"{msg}{gen_name} ({on}-{to}):" if on != to else f"Непрочитанный чат {gen_name}:"
            if (counter + 1) % 6 == 0:
                vk.messages.send(user_id=my_id, message=msg, keyboard=kUnreadChats.get_keyboard(), random_id=0)
                kUnreadChats = kb.VkKeyboard(inline=True)
                kUnreadChats.add_button("В главное меню", "primary")
                vk.messages.send(user_id=my_id, message='<3', keyboard=kUnreadChats.get_keyboard(), random_id=0)
            else:
                kUnreadChats.add_line()
                kUnreadChats.add_button("В главное меню", "primary")
                vk.messages.send(user_id=my_id, message=msg, keyboard=kUnreadChats.get_keyboard(), random_id=0)
        counter += 1


def getInfo(bInfo):
    global info
    info = []
    kInfo = ''
    kInfoList = []
    counter = 0
    for i in range(len(tokens)):
        if counter == 0:
            kInfo = kb.VkKeyboard(inline=True)
        try:
            chats = requests.get(f"https://api.vk.com/method/messages.getConversations?filter=unread&count=100&access_token={tokens[i]}&v={V}").json()["response"]["items"]
            if chats:
                if counter > 0 and counter % 3 == 0:
                    kInfo.add_line()
                info.append([i, token_names[i],
                             {chat['conversation']['peer']['id']: chat['conversation']['unread_count'] for chat in
                              chats}])
                kInfo.add_button(token_names[i], 'positive')
                counter += 1
                if counter == 10:
                    counter = 0
                    kInfoList.append(kInfo.get_keyboard())
            elif not bInfo:  # если непрочитанных нет, но вызвано "Все аккаунты"
                if counter > 0 and counter % 3 == 0:
                    kInfo.add_line()
                kInfo.add_button(token_names[i], 'secondary')
                counter += 1
                if counter == 10:
                    counter = 0
                    kInfoList.append(kInfo.get_keyboard())
        except:
            if counter > 0 and counter % 3 == 0:
                kInfo.add_line()
            kInfo.add_button(token_names[i], 'negative')
            counter += 1
            if counter == 10:
                counter = 0
                kInfoList.append(kInfo.get_keyboard())
    if kInfo.lines[0]:
        kInfoList.append(kInfo.get_keyboard())
    print(info)
    return kInfoList


def getActiveAccounts():
    if not len(ids):
        vk.messages.send(user_id=my_id, message=f'Ты настолько лох, что у тебя даже нет аккаунтов 😂', keyboard=kStart,
                         random_id=0)
        return
    kOpenAccount = kb.VkKeyboard(inline=True)
    i = 0
    kOpenAccount.add_openlink_button(token_full_names[i], f"https://vk.com/id{ids[i]}")
    if len(ids) == 1:
        vk.messages.send(user_id=my_id, message=f'Ссылка на аккаунт', keyboard=kOpenAccount.get_keyboard(), random_id=0)
    for i in range(1, len(ids)):
        if i % 6 == 0:
            vk.messages.send(user_id=my_id, message=f'Ссылки на аккаунты ({i - 5}-{i})',
                             keyboard=kOpenAccount.get_keyboard(), random_id=0)
            kOpenAccount = kb.VkKeyboard(inline=True)
            kOpenAccount.add_openlink_button(token_full_names[i], f"https://vk.com/id{ids[i]}")
        else:
            kOpenAccount.add_line()
            kOpenAccount.add_openlink_button(token_full_names[i], f"https://vk.com/id{ids[i]}")
        if i == len(ids) - 1:
            on = i + 1 - i % 6
            to = i + 1
            msg = "Ссылки на аккаунты ("
            msg = f"{msg}{on}-{to})" if on != to else f"Ссылка на аккаунт ({on})"
            vk.messages.send(user_id=my_id, message=msg, keyboard=kOpenAccount.get_keyboard(), random_id=0)
    vk.messages.send(user_id=my_id, message='Главное меню', keyboard=kStart, random_id=0)


def getChatName(idd):
    if idd < 0:
        name = vk.groups.getById(group_id=-idd)[0]["name"]
        if len(name) > 23:
            name = name[:20] + '...'
    elif idd > 2000000000:
        name = requests.get(
            f"https://api.vk.com/method/messages.getChat?chat_id={idd - 2000000000}&access_token={tokens[account_index]}&v={V}").json()[
            "response"]["title"]
        if len(name) > 23:
            name = name[:20] + '...'
    else:
        name = vk.users.get(user_ids=idd)[0]
        name = name['first_name'] + ' ' + name['last_name']
    return name


if __name__ == '__main__':
    main()
